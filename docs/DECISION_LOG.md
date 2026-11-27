# DECISION_LOG — decisões do Atlaz

<!-- atlaz:estado:inicio -->
<!-- atlaz: gerado_em=27/11/2026 fonte=atlaz.py hash=cad0d564 -->
**Estado dos registros** (6 no total, 0 🔵 abertos). Tabela gerada; não editar à mão.

| ID | Título | Estado | Data |
|---|---|---|---|
| ADR-001 | Links markdown relativos, nunca wikilinks | 🟢 Congelada | 20/09/2026 |
| ADR-002 | Modo cópia e modo fonte são os dois modos válidos, declarados pelo projeto | 🟡 Validada | 21/09/2026 |
| ADR-003 | A ferramenta é quem edita o que ela gera; hash diz se está fresco | 🟡 Validada | 21/09/2026 |
| ADR-004 | Regra de mudança: só entra na SPEC o que serve a mais de um tipo de projeto | 🟡 Validada | 21/09/2026 |
| ADR-005 | Ferramenta v0.2: onze correções do atlaz.py | 🟡 Validada | 23/09/2026 |
| ADR-006 | v0.3: primeira versão pública | 🟡 Validada | 27/11/2026 |
<!-- atlaz:estado:fim -->

Formato: ADR-NNN, data, estado (🔵 Aberta / 🟡 Validada / 🟢 Congelada), decisão, motivo, alternativas rejeitadas, impacto. Decisão nunca é apagada: mudança registra anterior → nova → motivo.

Este registro começa na versão pública (v0.3). As decisões anteriores foram reescritas sem os detalhes dos projetos internos, com as mesmas datas e o mesmo conteúdo técnico.

## ADR-001 — Links markdown relativos, nunca wikilinks
**Data:** 20/09/2026 · **Estado:** 🟢 Congelada
**Decisão:** `[Nome](caminho/relativo.md)`.
**Motivo:** o Obsidian lê os dois formatos e desenha o grafo dos dois; GitHub, VS Code e agentes só leem o primeiro. Link por caminho não confunde dois arquivos com o mesmo nome. Neutralidade tecnológica.
**Alternativas rejeitadas:** `[[wikilink]]` (bonito só no Obsidian).

## ADR-002 — Modo cópia e modo fonte são os dois modos válidos, declarados pelo projeto
**Data:** 21/09/2026 · **Estado:** 🟡 Validada
**Decisão:** o projeto declara em `atlaz.json` se o markdown é cópia (gerado de um banco, regenerável, não editar) ou fonte (é a verdade, editar é normal). A ferramenta se comporta igual nos dois; a diferença é quem tem permissão de escrever.
**Motivo:** um assistente que guarda a memória num banco precisa do modo cópia; um repositório de documentação precisa do modo fonte. Os dois estão certos. Forçar um modo só quebraria um deles.
**Alternativas rejeitadas:** "sempre cópia" (obriga todo projeto a ter banco); "sempre fonte" (onde há banco, editar o `.md` cria uma segunda fonte de verdade).

## ADR-003 — A ferramenta é quem edita o que ela gera; hash diz se está fresco
**Data:** 21/09/2026 · **Estado:** 🟡 Validada
**Decisão:** índices, "Veja também", tabelas de estado e linha do tempo são gerados, carimbados com data e hash, e nunca editados à mão. A ferramenta é idempotente.
**Motivo:** o que é editado à mão e também gerado diverge em silêncio. O hash permite saber se o bloco corresponde ao conteúdo atual sem reler tudo.
**Alternativas rejeitadas:** gerar uma vez e deixar o humano manter (morre em duas semanas).

## ADR-004 — Regra de mudança: só entra na SPEC o que serve a mais de um tipo de projeto
**Data:** 21/09/2026 · **Estado:** 🟡 Validada
**Decisão:** necessidade de um projeto só vira opção no `atlaz.json`, não regra da SPEC.
**Motivo:** evita que o Atlaz vire a cópia genérica de um projeto só.

## ADR-005 — Ferramenta v0.2: onze correções do atlaz.py
**Data:** 23/09/2026 · **Estado:** 🟡 Validada
**Contexto:** um repositório usou uma cópia da v0.1, achou defeitos no uso e os corrigiu com testes. As correções voltaram para a fonte. Cada uma está marcada `[v0.2 Cn]` no código:
- **C1 · `--buscar` sem a RAIZ.** `atlaz.py --buscar termo` tomava o termo como RAIZ e devolvia 0 ocorrências em silêncio. O valor de `--buscar` nunca é a RAIZ.
- **C2 · Lint de link para o que não é `.md`.** Agora todo link relativo é conferido (código, dado, imagem, pasta); URL, `mailto:` e âncora ficam fora.
- **C3 · "?" dentro de URL não é acento trocado.** URL e destino de link saem da linha antes do teste.
- **C4 · `--lint` não cria pasta.** Só verificando, ele criava a pasta da TIMELINE quando ela não existia.
- **C5 · Descrição com chave por caminho.** Em `descricoes`, a chave pode ser o caminho relativo à raiz, que vence o nome.
- **C6 · Subpasta só com código ou dado entra no mapa.** Pasta com `.py` ou `.json` e nenhum `.md` ganha INDEX.
- **C7 · `--buscar` no Windows com ripgrep.** O "C:" do caminho absoluto quebrava a leitura da saída do `rg`. Uma regex separa caminho, linha e texto.
- **C8 · Saída em UTF-8 no pipe.** No Windows, a saída lida por pipe chegava com acento trocado.
- **C9 · `--help`, `-h` e argumento desconhecido não aplicam nada.** Antes, pedir ajuda aplicava a ferramenta. Agora a ajuda sai com 0 e o uso errado sai com 2, antes de escrever qualquer coisa.
- **C10 · Pasta intermediária e pasta oculta.** Toda pasta no caminho até uma pasta indexada ganha INDEX, e nada dentro de pasta oculta vira índice.
- **C11 · Arquivo que o git ignora fica fora do INDEX.** É local (segredo, peso, log), e o link quebraria em todo clone.

**Motivo:** a fonte da ferramenta é o Atlaz. Correção que fica só numa cópia se perde na próxima recópia. Dez das onze fazem a ferramenta cumprir o que a SPEC já dizia; a C5 é opção nova do `atlaz.json`, que a ADR-004 permite.
**Alternativas rejeitadas:** deixar as correções só na cópia (a cópia e a fonte divergiriam); trocar o leitor de argumentos por `argparse` (mudaria o texto de ajuda e as mensagens sem ganho medido).

## ADR-006 — v0.3: primeira versão pública
**Data:** 27/11/2026 · **Estado:** 🟡 Validada
**Decisão:** abrir o código sob a licença MIT, com:
- padrões da ferramenta genéricos: a linha do tempo lê só `docs/DECISION_LOG.md`, e caminho vazio desliga uma fonte (antes, os padrões apontavam para a estrutura de um repositório interno);
- o texto gerado no topo da TIMELINE passou a dizer só de onde os eventos vêm, sem nomes internos;
- **só dentro da RAIZ:** caminho do `atlaz.json` que sai da RAIZ (com `..` ou absoluto) é uso errado e sai com 2; a ferramenta não escreve num `.md` que é link simbólico para fora dela. Motivo: uma ferramenta pública roda em repositórios de terceiros, e um `atlaz.json` malicioso fazia a ferramenta escrever fora da pasta (achado da revisão de segurança, conferido com teste);
- `atlaz.json` inválido também é uso errado e sai com 2, antes de escrever qualquer coisa (antes, a ferramenta quebrava com 1);
- a busca trata o termo como texto literal também com o ripgrep (`-F`); antes, com ripgrep o termo virava regex e o resultado mudava conforme a máquina;
- saiu do código a descrição automática de um tipo de arquivo que só um projeto usava;
- [AGENTS.md](../AGENTS.md) como entrada para agentes (o [CLAUDE.md](../CLAUDE.md) aponta para ele);
- a SPEC alinhada ao código: órfão é aviso do lint, não erro (seção 9); o "Veja também" não leva hash (seção 7); Python 3.7 ou mais novo; a seção 14 ganhou a tabela das chaves e os formatos reconhecidos;
- documentação sem citar projetos internos.
**Motivo:** a convenção e a ferramenta servem a qualquer projeto com muitos arquivos de texto e agentes de IA. Neutralidade (ADR-001) também vale para quem pode usar.
**Alternativas rejeitadas:** publicar com o histórico interno (expõe detalhes de projetos fechados); manter fechado (a ferramenta não tem nada de sigiloso).
**Impacto:** quem usa uma cópia com `atlaz.json` próprio não muda nada. Quem dependia dos padrões antigos da TIMELINE precisa declarar os caminhos no `atlaz.json`.

<!-- atlaz:veja-tambem:inicio -->
## Veja também

Índice desta pasta: [INDEX.md](INDEX.md)
Aponta para: [AGENTS.md](../AGENTS.md) · [CLAUDE.md](../CLAUDE.md)
Citado por: [AGENTS.md](../AGENTS.md) · [README.md](../README.md) · [SPEC.md](../SPEC.md) · [ADOTAR.md](ADOTAR.md) · [ORIGEM.md](ORIGEM.md) · [TIMELINE.md](TIMELINE.md)
_(seção gerado por atlaz.py; não editar à mão)_
<!-- atlaz:veja-tambem:fim -->
