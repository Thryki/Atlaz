# -*- coding: utf-8 -*-
# Atlaz v0.3, 27/11/2026: primeira versão pública (licença MIT). https://github.com/Thryki/Atlaz
# Esta é a fonte da ferramenta: projetos que usam uma cópia recopiam daqui.
# As 11 correções da v0.2 estão marcadas "[v0.2 Cn]" no código e descritas em docs/DECISION_LOG.md, ADR-005.
"""
atlaz.py — a ferramenta do Atlaz: memória em camadas em arquivos de texto. Versão 0.3 (27/11/2026).

Propósito (nas palavras do fundador): o agente encontra o que precisa o mais rápido
possível, com o menor custo possível, no meio de muita coisa.

O que faz, nesta ordem, num repositório:
  1. converte referências a arquivos .md em links markdown relativos (Obsidian, GitHub,
     VS Code e qualquer agente leem);
  2. gera INDEX.md em cada pasta (camada do meio da escada: "o que é" e "quando ler");
  3. escreve/atualiza a seção "Veja também" em cada documento (aponta para / citado por);
  4. gera TIMELINE.md (segundo caminho de acesso: por data);
  5. gera a tabela de estado no topo dos arquivos de registro (Registry, Decision Log);
  6. carimba tudo que gera com data e hash (pra saber se está fresco);
  7. lint: link quebrado (para .md e para qualquer outro arquivo ou pasta), órfão (ponta
     solta), nome duplicado, acento virado "?" (fora de URL), arquivo acima do orçamento
     da camada.

Uso:
  python atlaz.py [RAIZ]            aplica tudo e roda o lint (RAIZ = pasta atual se omitida)
  python atlaz.py [RAIZ] --lint     só verifica: não escreve nada nem cria pasta
  python atlaz.py [RAIZ] --buscar "termo"   busca por palavra, ranqueada pela escada
                                    (ex.: python atlaz.py . --buscar termo; o termo nunca é a RAIZ)
  python atlaz.py --help            mostra este texto e sai (também -h), sem escrever nada

  Código de saída: 0 ok; 1 lint com erro (ou falha inesperada, como um .md fora de UTF-8);
  2 uso errado (opção desconhecida, mais de uma RAIZ, RAIZ que não é pasta, --buscar sem
  termo, atlaz.json inválido ou com caminho fora da RAIZ), e nesse caso nada foi escrito.

Configuração opcional: um arquivo atlaz.json na raiz (ver SPEC.md, seção "Configuração").
Sem ele, a ferramenta usa os padrões abaixo.

Regras: nunca toca em arquivos listados em "nao_tocar", nem em blocos de código, nem em
frontmatter YAML. Tudo que gera diz que foi gerado e por quem.
"""
import io, os, re, sys, json, hashlib, datetime, subprocess, urllib.parse

VERSAO = '0.3'

# [v0.2 C8] saída lida por pipe (agente, CI) vai em UTF-8: no Windows ela saía na página de código do console
# e o acento chegava como "\ufffd" a quem lia a busca ou o lint por pipe. Vale também para a mensagem de
# erro de uso (stderr).
for _fluxo in (sys.stdout, sys.stderr):
    if not _fluxo.isatty():
        try: _fluxo.reconfigure(encoding='utf-8', errors='replace')
        except Exception: pass

# ----------------------------------------------------------------- argumentos
# [v0.2 C1] o valor de --buscar não é a raiz: antes, "atlaz.py --buscar termo" tomava "termo" como RAIZ
# e devolvia 0 ocorrências em silêncio. O jeito certo: "atlaz.py . --buscar termo" (ou sem a RAIZ).
# [v0.2 C9] "--help", "-h" e qualquer argumento desconhecido APLICAVAM a ferramenta (a opção era ignorada e o
# modo de escrita rodava): dois agentes regravaram a árvore sem querer pedindo --help. Agora --help/-h mostram o uso e
# saem com 0; opção desconhecida, mais de uma RAIZ, RAIZ que não é pasta ou --buscar sem termo saem com 2. Nos dois
# casos, antes de ler a configuração ou escrever qualquer coisa.
USO = __doc__[__doc__.index('Uso:'):__doc__.index('Configuração opcional')].rstrip() + '\n'
def _erro_de_uso(msg):
    sys.stderr.write('atlaz.py: erro: %s (nada foi escrito)\n%s' % (msg, USO)); sys.exit(2)
def _ler_argumentos(argv):
    raiz, lint, buscar, i = None, False, None, 0
    while i < len(argv):
        a = argv[i]
        if a in ('--help', '-h'):
            sys.stdout.write(__doc__.lstrip()); sys.exit(0)
        if a == '--lint': lint = True
        elif a == '--buscar':
            if i + 1 >= len(argv): _erro_de_uso('--buscar sem o termo')
            buscar = argv[i + 1]; i += 1
        elif a.startswith('-'): _erro_de_uso('argumento desconhecido: %s' % a)
        elif raiz is not None: _erro_de_uso('mais de uma RAIZ: %s e %s' % (raiz, a))
        else: raiz = a
        i += 1
    if raiz is not None and not os.path.isdir(raiz): _erro_de_uso('RAIZ não é uma pasta: %s' % raiz)
    return (os.path.abspath(raiz) if raiz is not None else os.getcwd()), lint, buscar
ROOT, LINT_ONLY, BUSCAR = _ler_argumentos(sys.argv[1:])
TODAY = datetime.date.today().strftime('%d/%m/%Y')

# [v0.3] nada é lido do atlaz.json nem escrito fora da RAIZ: nem por caminho com "..", nem por caminho absoluto,
# nem por link simbólico. Um atlaz.json de um repositório de terceiros não pode mandar a ferramenta escrever fora dele.
_RAIZ_REAL = os.path.normcase(os.path.realpath(ROOT))
def dentro_da_raiz(p):
    r = os.path.normcase(os.path.realpath(p))
    return r == _RAIZ_REAL or r.startswith(_RAIZ_REAL.rstrip(os.sep) + os.sep)

# ----------------------------------------------------------------- configuração
DEFAULT_CFG = {
    "modo": "fonte",                      # "fonte": o markdown é a verdade | "copia": gerado de um banco
    "entradas": ["README.md", "CLAUDE.md", "AGENTS.md"],   # topo da escada; nunca contam como órfãos
    "nao_tocar": [],                      # arquivos que a ferramenta nunca reescreve
    "ignorar_pastas": [".git", ".obsidian", "node_modules", "__pycache__", ".venv"],
    "descricoes": {},                     # nome.md -> ["o que é", "quando ler"]; [v0.2 C5] também caminho/relativo.md, que vence o nome
    "pastas": {},                         # caminho/relativo -> título do índice
    "estado": [],                         # arquivos de registro que ganham tabela de estado no topo
    "indice_raiz": False,                 # gera INDEX.md também na raiz (quando o README não faz esse papel)
    "orcamento": {                        # linhas máximas por camada (aviso, não erro)
        "INDEX.md": 120, "CURRENT.md": 80, "TIMELINE.md": 2000, "*.md": 900
    },
    "timeline": {                         # de onde a TIMELINE tira eventos
        "arquivo": "docs/TIMELINE.md",
        "decisoes": "docs/DECISION_LOG.md",       # registro de decisões (## ADR-NNN)
        "registros": "",                            # registro de perguntas (### Registry #NNN); vazio = desligado
        "discordancias": "",                        # placar de discordâncias (### DIS-NNN); vazio = desligado
        "sessoes_glob": ""                          # prefixo dos arquivos de sessão; vazio = desligado
    }
}
cfg = dict(DEFAULT_CFG)
cfg_path = os.path.join(ROOT, 'atlaz.json')
if os.path.exists(cfg_path):
    # [v0.3] atlaz.json inválido é uso errado: sai com 2 antes de escrever qualquer coisa.
    try: user = json.load(io.open(cfg_path, encoding='utf-8'))
    except ValueError as e: _erro_de_uso('atlaz.json inválido: %s' % e)
    if not isinstance(user, dict): _erro_de_uso('atlaz.json inválido: o topo tem de ser um objeto {...}')
    for k, v in user.items():
        if isinstance(v, dict) and isinstance(cfg.get(k), dict):
            merged = dict(cfg[k]); merged.update(v); cfg[k] = merged
        else:
            cfg[k] = v
for _c in [cfg['timeline'].get(k) for k in ('arquivo', 'decisoes', 'registros', 'discordancias')] + list(cfg['estado']):
    if _c and not dentro_da_raiz(os.path.join(ROOT, _c)): _erro_de_uso('caminho fora da RAIZ no atlaz.json: %s' % _c)
SKIP_DIRS = set(cfg['ignorar_pastas'])
NO_TOUCH = set(cfg['nao_tocar'])
ENTRY_POINTS = set(cfg['entradas'])
DESCR = {k: tuple(v) for k, v in cfg['descricoes'].items()}
FOLDER_TITLE = cfg['pastas']
MARCA = 'gerado por atlaz.py'

def rel(a_dir, b_path):
    return os.path.relpath(b_path, a_dir).replace('\\', '/')
def read(p): return io.open(p, encoding='utf-8').read()
def write(p, s):
    if LINT_ONLY: return
    if not dentro_da_raiz(p):   # [v0.3] ex.: um .md que é link simbólico para fora da RAIZ
        sys.stderr.write('atlaz.py: aviso: não escrevi fora da RAIZ: %s\n' % p); return
    io.open(p, 'w', encoding='utf-8', newline='\n').write(s)
def h8(s): return hashlib.sha1(s.encode('utf-8')).hexdigest()[:8]
def carimbo(fonte, conteudo_base):
    return '<!-- atlaz: gerado_em=%s fonte=%s hash=%s -->' % (TODAY, fonte, h8(conteudo_base))

# ----------------------------------------------------------------- inventário
md_files = []
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    for fn in fns:
        if fn.lower().endswith('.md'):
            md_files.append(os.path.join(dp, fn))
md_files.sort()
by_base = {}
for p in md_files:
    by_base.setdefault(os.path.basename(p), []).append(p)

# ----------------------------------------------------------------- busca
def buscar(termo):
    """Busca por palavra, ranqueada pela escada: INDEX > CURRENT > topics > daily > resto."""
    def peso(path):
        b = os.path.basename(path); d = path.replace('\\', '/')
        if b == 'INDEX.md': return 0
        if b == 'CURRENT.md': return 1
        if '/topics/' in d: return 2
        if '/daily/' in d: return 3
        if b in ('TIMELINE.md', 'REGISTRY.md', 'DECISION_LOG.md'): return 4
        return 5
    hits = []
    rg = None
    for cand in ('rg', 'rg.exe'):
        try:
            subprocess.run([cand, '--version'], capture_output=True, check=True); rg = cand; break
        except Exception: pass
    if rg:
        # [v0.3] -F: o termo é texto literal, como na busca sem ripgrep (antes, com ripgrep, virava regex).
        out = subprocess.run([rg, '-n', '-i', '-F', '--no-heading', '--glob', '*.md', '--', termo, ROOT],
                             capture_output=True, text=True, encoding='utf-8', errors='replace').stdout
        for line in out.splitlines():
            # [v0.2 C7] era line.split(':', 2): no Windows o caminho absoluto começa com "C:", o número da
            # linha caía no caminho e o int() quebrava (ValueError) assim que o ripgrep estivesse instalado.
            m = re.match(r'^(.*?):(\d+):(.*)$', line)
            if m: hits.append((m.group(1), int(m.group(2)), m.group(3).strip()))
    else:
        t = termo.lower()
        for p in md_files:
            for i, l in enumerate(read(p).split('\n')):
                if t in l.lower(): hits.append((p, i + 1, l.strip()))
    hits.sort(key=lambda x: (peso(x[0]), x[0], x[1]))
    print('atlaz buscar "%s" — %d ocorrência(s), ranqueadas pela escada (índice primeiro)' % (termo, len(hits)))
    last = None
    for p, n, l in hits[:80]:
        r = rel(ROOT, p)
        if r != last: print('\n' + r); last = r
        print('  %5d  %s' % (n, l[:140]))
    if len(hits) > 80: print('\n... e mais %d. Refine o termo.' % (len(hits) - 80))
if BUSCAR is not None:
    buscar(BUSCAR); sys.exit(0)

# ----------------------------------------------------------------- 1. links
VT_INI, VT_FIM = '<!-- atlaz:veja-tambem:inicio -->', '<!-- atlaz:veja-tambem:fim -->'
ES_INI, ES_FIM = '<!-- atlaz:estado:inicio -->', '<!-- atlaz:estado:fim -->'
LINK_RE = re.compile(r'\[[^\]]*\]\([^)]*\)')
def convert_links(path, text):
    d = os.path.dirname(path)
    names = sorted([b for b, ps in by_base.items() if len(ps) == 1 and b != 'INDEX.md'], key=len, reverse=True)
    out, fence, gerado = [], False, False
    lines = text.split('\n'); fm_end = -1
    if lines and lines[0].strip() == '---':
        for i in range(1, len(lines)):
            if lines[i].strip() == '---': fm_end = i; break
    for li, line in enumerate(lines):
        if li <= fm_end: out.append(line); continue
        if line.strip().startswith('```'):
            fence = not fence; out.append(line); continue
        if line.strip() in (ES_INI, VT_INI): gerado = True
        if line.strip() in (ES_FIM, VT_FIM): gerado = False; out.append(line); continue
        if fence or gerado or line.lstrip().startswith('<!--'): out.append(line); continue
        holes = []
        def hole(m):
            holes.append(m.group(0)); return '\x00%d\x00' % (len(holes) - 1)
        work = LINK_RE.sub(hole, line)
        for b in names:
            tgt = by_base[b][0]
            if tgt == path: continue
            r = rel(d, tgt)
            work = re.sub(r'`((?:[\w\-.]+/)*' + re.escape(b) + r')`', lambda m: '[%s](%s)' % (m.group(1), r), work)
            work = re.sub(r'(?<![\w/\[\(`.])((?:[\w\-.]+/)*' + re.escape(b) + r')(?![\w\)\]`])', lambda m: '[%s](%s)' % (m.group(1), r), work)
        work = re.sub(r'\x00(\d+)\x00', lambda m: holes[int(m.group(1))], work)
        out.append(work)
    return '\n'.join(out)

changed = 0
for p in md_files:
    b = os.path.basename(p)
    if b in NO_TOUCH or rel(ROOT, p) in NO_TOUCH or b == 'INDEX.md': continue
    t = read(p); n = convert_links(p, t)
    if n != t: write(p, n); changed += 1

# ----------------------------------------------------------------- 2. grafo
VT_INI, VT_FIM = '<!-- atlaz:veja-tambem:inicio -->', '<!-- atlaz:veja-tambem:fim -->'
ES_INI, ES_FIM = '<!-- atlaz:estado:inicio -->', '<!-- atlaz:estado:fim -->'
def strip_marks(t):
    t = re.sub(re.escape(VT_INI) + r'.*?' + re.escape(VT_FIM) + r'\n?', '', t, flags=re.S)
    t = re.sub(re.escape(ES_INI) + r'.*?' + re.escape(ES_FIM) + r'\n?', '', t, flags=re.S)
    return t
def links_of(path):
    d = os.path.dirname(path); res = []
    t = strip_marks(read(path))
    t = re.sub(r'```.*?```', '', t, flags=re.S)      # blocos de código não contam
    t = re.sub(r'`[^`\n]*`', '', t)                  # código inline não conta
    for m in re.finditer(r'\]\(([^)\s#]+\.md)(?:#[^)]*)?\)', t):
        tgt = m.group(1)
        if tgt.startswith('http'): continue
        res.append(os.path.normpath(os.path.join(d, tgt)))
    return res
outgoing = {p: sorted(set(links_of(p))) for p in md_files}
incoming = {p: [] for p in md_files}
broken = []
for p, ts in outgoing.items():
    for t in ts:
        if t in incoming: incoming[t].append(p)
        elif not os.path.exists(t): broken.append((p, t))
# [v0.2 C2] link relativo para o que não é .md (código, dado, imagem, pasta) também é verificado.
# Antes só .md contava, e um INDEX apontando para um .py inexistente passava no lint com 0.
# Não entra no grafo (Veja também, órfãos): só no lint de link quebrado.
ESQUEMA_RE = re.compile(r'^[A-Za-z][A-Za-z0-9+.\-]*:')
def outros_links(path):
    d = os.path.dirname(path); res = []
    t = strip_marks(read(path))
    t = re.sub(r'```.*?```', '', t, flags=re.S)
    t = re.sub(r'`[^`\n]*`', '', t)
    for m in re.finditer(r'\]\((?:<([^>\n]+)>|([^)\s]+))[^)\n]*\)', t):
        tgt = re.split(r'[#?]', m.group(1) or m.group(2))[0]
        if not tgt or ESQUEMA_RE.match(tgt) or tgt.lower().endswith('.md'): continue   # âncora, URL, mailto:; .md já foi visto acima
        tgt = urllib.parse.unquote(tgt)
        base = ROOT if tgt.startswith('/') else d
        res.append(os.path.normpath(os.path.join(base, tgt.lstrip('/'))))
    return res
for p in md_files:
    for t in sorted(set(outros_links(p))):
        if not os.path.exists(t): broken.append((p, t))

# ----------------------------------------------------------------- 3. veja também
def veja_tambem(p):
    d = os.path.dirname(p)
    parts = ['', VT_INI, '## Veja também', '']
    if d == ROOT: parts.append('Índice geral: [INDEX.md](INDEX.md)' if os.path.exists(os.path.join(ROOT, 'INDEX.md')) else 'Índice: [docs/INDEX.md](docs/INDEX.md)')
    elif os.path.exists(os.path.join(d, 'SKILL.md')): parts.append('Índice das skills: [INDEX.md](../INDEX.md)')
    else: parts.append('Índice desta pasta: [INDEX.md](INDEX.md)')
    outs = [t for t in outgoing[p] if os.path.basename(t) != 'INDEX.md' and t != p]
    ins = [t for t in incoming[p] if os.path.basename(t) != 'INDEX.md' and t != p]
    if outs: parts.append('Aponta para: ' + ' · '.join('[%s](%s)' % (os.path.basename(t), rel(d, t)) for t in outs))
    if ins: parts.append('Citado por: ' + ' · '.join('[%s](%s)' % (os.path.basename(t), rel(d, t)) for t in ins))
    parts.append('_(seção %s; não editar à mão)_' % MARCA)
    parts.append(VT_FIM); parts.append('')
    return '\n'.join(parts)
for p in md_files:
    b = os.path.basename(p)
    if b in NO_TOUCH or rel(ROOT, p) in NO_TOUCH or b == 'INDEX.md' or (os.path.dirname(p) == ROOT and b in ENTRY_POINTS): continue
    t = read(p)
    t = re.sub(re.escape(VT_INI) + r'.*?' + re.escape(VT_FIM) + r'\n?', '', t, flags=re.S).rstrip('\n') + '\n'
    write(p, t + veja_tambem(p))

# ----------------------------------------------------------------- 4. INDEX.md por pasta
def descr(fn, caminho=None):
    # [v0.2 C5] a chave pode ser o caminho relativo à raiz ("docs/relatorio.py"), que vence o nome:
    # nomes repetidos em pastas diferentes (README.md, relatorio.py, __init__.py) ganham descrições próprias.
    if caminho and caminho in DESCR: return DESCR[caminho]
    if fn in DESCR: return DESCR[fn]
    if fn == 'SKILL.md': return ('procedimento executável pela IA', 'quando o gatilho da skill acontecer')
    if fn == 'CURRENT.md': return ('o que está acontecendo agora', 'segundo degrau da escada, logo depois do índice')
    if fn == 'TIMELINE.md': return ('tudo por data', 'quando a pergunta for "quando?"')
    return ('', '')
def first_line_descr(path):
    """Quando não há descrição configurada: primeira citação (>) ou primeiro parágrafo depois do H1."""
    t = strip_marks(read(path))
    m = re.search(r'^description:\s*(.+)$', t, re.M)
    if m: return m.group(1).strip()
    m = re.search(r'^>\s*\*?\*?(?:Status|Estado)?[^\n]*\n', t, re.M)
    body = re.sub(r'^---\n.*?\n---\n', '', t, flags=re.S)
    for line in body.split('\n'):
        s = line.strip()
        if not s or s.startswith('#') or s.startswith('<!--') or s.startswith('|') or s.startswith('```'): continue
        s = re.sub(r'^>\s*', '', s); s = re.sub(r'\*\*', '', s)
        return (s[:150] + '…') if len(s) > 150 else s
    return ''
# [v0.2 C6] subpasta só com código ou dado (.py/.json, sem .md) também ganha INDEX e aparece no índice
# da pasta de cima. Antes ficava fora do mapa (num projeto real, uma subpasta com um script só não aparecia em índice nenhum).
INDEXAVEL = ('.md', '.py', '.json')
code_dirs = set()
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in SKIP_DIRS and not d.startswith('.')]
    if dp != ROOT and any(fn.endswith(INDEXAVEL) for fn in fns): code_dirs.add(dp)
folders = ({os.path.dirname(p) for p in md_files if os.path.dirname(p) != ROOT} | code_dirs |
           {os.path.join(ROOT, d) for d in os.listdir(ROOT) if os.path.isdir(os.path.join(ROOT, d)) and d not in SKIP_DIRS and not d.startswith('.')})
# [v0.2 C10] toda pasta intermediária também ganha INDEX (senão o "Subir um nível" da filha aponta para um
# INDEX que não existe), e nada dentro de pasta oculta (.pytest_cache/, .github/...) vira índice, em qualquer nível.
for f in list(folders):
    f = os.path.dirname(f)
    while f != ROOT and len(f) > len(ROOT): folders.add(f); f = os.path.dirname(f)
folders = sorted(f for f in folders if not any(x.startswith('.') for x in rel(ROOT, f).split('/'))
                 and not os.path.exists(os.path.join(f, 'SKILL.md')))
if cfg.get('indice_raiz'): folders = [ROOT] + folders
# [v0.2 C11] arquivo que o git ignora não entra no INDEX: é local (segredo, peso, log) e o link quebraria em
# todo clone. Caso típico: um arquivo local de configuração, listado no .gitignore, não pode aparecer no INDEX da
# pasta. Pergunta ao próprio git (check-ignore, uma chamada só); fora de um repositório git, ou sem git,
# lista tudo.
def ignorados_pelo_git(caminhos):
    if not caminhos: return set()
    try:
        r = subprocess.run(['git', '-C', ROOT, 'check-ignore', '--stdin', '-z'],
                           input='\0'.join(rel(ROOT, p) for p in caminhos) + '\0',
                           capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
    except Exception:
        return set()
    if r.returncode not in (0, 1): return set()
    return {os.path.normcase(os.path.normpath(os.path.join(ROOT, x))) for x in r.stdout.split('\0') if x}
IGNORADOS = ignorados_pelo_git([os.path.join(f, e) for f in folders for e in os.listdir(f)
                                if not e.startswith('.') and e.endswith(INDEXAVEL) and os.path.isfile(os.path.join(f, e))])
for f in folders:
    key = rel(ROOT, f)
    title = FOLDER_TITLE.get(key, os.path.basename(ROOT) if key == '.' else key)
    rows = []
    for e in sorted(os.listdir(f)):
        fp = os.path.join(f, e)
        if e.startswith('.') or e == 'INDEX.md': continue
        if os.path.normcase(os.path.normpath(fp)) in IGNORADOS: continue
        if os.path.isdir(fp):
            if e in SKIP_DIRS: continue
            sub_skill = os.path.join(fp, 'SKILL.md'); sub_idx = os.path.join(fp, 'INDEX.md')
            if os.path.exists(sub_skill):
                rows.append('| [%s/](%s) | %s | quando o gatilho acontecer |' % (e, rel(f, sub_skill), first_line_descr(sub_skill)))
            elif fp in folders or os.path.exists(sub_idx):   # [v0.2 C6] era: só se tivesse .md
                rows.append('| [%s/](%s) | %s | pasta: abra o índice dela |' % (e, rel(f, sub_idx), FOLDER_TITLE.get(rel(ROOT, fp), '')))
            continue
        if not (e.endswith('.md') or e.endswith('.py') or e.endswith('.json')): continue
        o, q = descr(e, rel(ROOT, fp))
        if not o and e.endswith('.md'): o = first_line_descr(fp)
        rows.append('| [%s](%s) | %s | %s |' % (e, e, o, q))
    if f == ROOT: up = None
    elif os.path.dirname(f) != ROOT: up = rel(f, os.path.join(os.path.dirname(f), 'INDEX.md'))
    else: up = '../INDEX.md' if cfg.get('indice_raiz') else '../README.md'
    body = '\n'.join(rows)
    lines = ['# INDEX — ' + title, '',
             carimbo('atlaz.py', body),
             '> Camada do meio da escada Atlaz: uma linha por arquivo, **o que é** e **quando ler**. Desça só até onde precisar. Não editar à mão.', '',
             '| Arquivo | O que é | Quando ler |', '|---|---|---|', body, '']
    if up: lines += ['Subir um nível: [%s](%s)' % (os.path.basename(up), up), '']
    write(os.path.join(f, 'INDEX.md'), '\n'.join(lines))

# ----------------------------------------------------------------- 5. TIMELINE
DATE_RE = re.compile(r'(\d{2})/(\d{2})/(\d{4})')
TL = cfg['timeline']
events = []
def add_event(datestr, tipo, oque):
    d, mo, y = datestr.split('/'); events.append((y + mo + d, datestr, tipo, oque))
tl_path = os.path.join(ROOT, TL['arquivo']); tl_dir = os.path.dirname(tl_path)
dl = os.path.join(ROOT, TL['decisoes'])
if os.path.exists(dl):
    txt = strip_marks(read(dl))
    for m in re.finditer(r'^## (ADR-\d+) — (.+?)\n(?:.*?\n)?\*\*Data:\*\* ([^·\n]+)', txt, re.M):
        dm = DATE_RE.search(m.group(3))
        if dm: add_event('%s/%s/%s' % dm.groups(), 'Decisão', '[%s](%s) — %s' % (m.group(1), rel(tl_dir, dl), m.group(2).strip()))
for p in md_files:
    b = os.path.basename(p); r = rel(ROOT, p)
    if TL['sessoes_glob'] and r.startswith(TL['sessoes_glob']):
        for m in re.finditer(r'^###? Registro da sessão (\d+) — (\d{2}/\d{2}/\d{4})', read(p), re.M):
            add_event(m.group(2), 'Sessão', '[%s](%s) — sessão %s' % (b, rel(tl_dir, p), m.group(1)))
    if TL['registros'] and r == TL['registros']:
        for m in re.finditer(r'^### (Registry #\d+) — (.+?)\n(?:.*?\n){0,3}?\*\*Origem:\*\*[^\n]*?(\d{2}/\d{2}/\d{4})', strip_marks(read(p)), re.M):
            add_event(m.group(3), 'Registro', '[%s](%s) — %s' % (m.group(1), rel(tl_dir, p), m.group(2).strip()))
    if TL['discordancias'] and r == TL['discordancias']:
        for m in re.finditer(r'^### (DIS-\d+) — (\d{2}/\d{2}/\d{4})', read(p), re.M):
            add_event(m.group(2), 'Discordância', '[%s](%s)' % (m.group(1), rel(tl_dir, p)))
events.sort()
if events or os.path.exists(tl_path):
    body = '\n'.join('| %s | %s | %s |' % (d, t, w) for _, d, t, w in events)
    tl = ['# TIMELINE — o projeto por data', '', carimbo('atlaz.py', body),
          '> Segundo caminho de acesso do Atlaz: por tempo, não por tema. Gerado a partir dos registros declarados no atlaz.json (decisões e, se houver, sessões, perguntas e discordâncias); não editar à mão.', '',
          '| Data | Tipo | O quê |', '|---|---|---|', body, '', 'Voltar: [INDEX.md](INDEX.md)', '']
    if not LINT_ONLY: os.makedirs(tl_dir, exist_ok=True)   # [v0.2 C4] --lint não cria pasta
    write(tl_path, '\n'.join(tl))

# ----------------------------------------------------------------- 6. tabela de estado
def estado_tabela(path):
    t = strip_marks(read(path))
    rows = []
    for m in re.finditer(r'^(#{2,3}) ((?:Registry #\d+|ADR-\d+|DIS-\d+|D-\d+|H-\d+)[^\n]*?) — ([^\n]+)\n(.*?)(?=^#{2,3} |\Z)', t, re.M | re.S):
        ident, title, body = m.group(2).strip(), m.group(3).strip(), m.group(4)
        st = re.search(r'\*\*(?:Status|Estado):\*\*\s*([^\n]+)', body)
        estado = st.group(1).strip() if st else ''
        estado = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', estado)   # sem links: a tabela é resumo
        estado = re.sub(r'\s+', ' ', estado)
        if len(estado) > 60: estado = estado[:57] + '…'
        dm = DATE_RE.search(title) or DATE_RE.search(body)
        data = '%s/%s/%s' % dm.groups() if dm else ''
        if re.match(r'^\d{2}/\d{2}/\d{4}$', title): title = ''
        rows.append('| %s | %s | %s | %s |' % (ident, title, estado, data))
    if not rows: return None
    body = '\n'.join(rows)
    abertos = sum(1 for r in rows if '🔵' in r)
    return '\n'.join([ES_INI, carimbo('atlaz.py', body),
                      '**Estado dos registros** (%d no total, %d 🔵 abertos). Tabela gerada; não editar à mão.' % (len(rows), abertos), '',
                      '| ID | Título | Estado | Data |', '|---|---|---|---|', body, ES_FIM, ''])
for r in cfg['estado']:
    p = os.path.join(ROOT, r)
    if not os.path.exists(p): continue
    t = read(p)
    t = re.sub(r'\n*' + re.escape(ES_INI) + r'.*?' + re.escape(ES_FIM) + r'\n*', '\n\n', t, flags=re.S)
    tab = estado_tabela(p)
    if not tab: continue
    # insere depois do H1 e da citação inicial (se houver), com exatamente uma linha em branco de cada lado
    lines = t.split('\n'); i = 0
    if lines and lines[0].startswith('# '): i = 1
    while i < len(lines) and (lines[i].strip() == '' or lines[i].startswith('>')): i += 1
    head = '\n'.join(lines[:i]).rstrip('\n'); rest = '\n'.join(lines[i:]).lstrip('\n')
    t = head + '\n\n' + tab.rstrip('\n') + '\n\n' + rest
    write(p, t)

# ----------------------------------------------------------------- 7. lint
orphans = [p for p in md_files if not incoming[p] and os.path.basename(p) not in ENTRY_POINTS and os.path.basename(p) != 'INDEX.md']
dups = {b: ps for b, ps in by_base.items() if len(ps) > 1 and b not in ('INDEX.md', 'SKILL.md', 'CURRENT.md', 'README.md')}
ENC_RE = re.compile(r'(\w\?\w)|(\s\?\s)|(\?\?)')
# [v0.2 C3] URL e destino de link saem antes do teste: "pagina?x=1" não é acento trocado.
URL_RE = re.compile(r'\]\([^)\n]*\)|<?https?://[^\s>)\]]+')
enc_bad = []
for p in md_files:
    if os.path.basename(p) in NO_TOUCH or rel(ROOT, p) in NO_TOUCH: continue
    for i, l in enumerate(read(p).split('\n')):
        if ENC_RE.search(URL_RE.sub('', l)): enc_bad.append((p, i + 1))
def orcamento_de(b):
    o = cfg['orcamento']
    return o.get(b, o.get('*.md', 900))
acima = []
for p in md_files:
    if os.path.basename(p) in NO_TOUCH or rel(ROOT, p) in NO_TOUCH: continue
    n = read(p).count('\n') + 1; lim = orcamento_de(os.path.basename(p))
    if n > lim: acima.append((p, n, lim))

print('atlaz —', 'lint' if LINT_ONLY else 'aplicado', '| modo:', cfg['modo'], '| arquivos .md:', len(md_files), '| links convertidos em', changed, 'arquivos')
print('links quebrados:', len(broken))
for p, t in broken: print('   ', rel(ROOT, p), '->', rel(ROOT, t))
print('órfãos (ninguém aponta para eles):', len(orphans))
for p in orphans: print('   ', rel(ROOT, p))
print('nomes duplicados:', len(dups))
for b, ps in dups.items(): print('   ', b, '->', ', '.join(rel(ROOT, x) for x in ps))
print('acento trocado por "?" (codificação):', len(enc_bad))
for p, i in enc_bad[:20]: print('   ', rel(ROOT, p), 'linha', i)
print('acima do orçamento da camada (aviso):', len(acima))
for p, n, lim in acima: print('   ', rel(ROOT, p), '%d linhas (limite %d)' % (n, lim))
sys.exit(1 if (broken or enc_bad) else 0)
