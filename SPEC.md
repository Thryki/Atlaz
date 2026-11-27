# SPEC — Atlaz v0.3

> **Status:** v0.3, primeira versão pública. Regra dura, orientação e futuro estão marcados em cada seção. As decisões por trás de cada regra estão no [DECISION_LOG.md](docs/DECISION_LOG.md).

## 1. O que é

Memória em camadas em arquivos de texto. O agente entra pelo mapa, desce um degrau por vez e **para quando tiver o suficiente**. O objetivo é achar o que precisa o mais rápido e mais barato possível no meio de muita coisa.

## 2. As camadas (regra dura)

Nomes fixos. Qualquer projeto usa os mesmos nomes; não inventa nome novo para camada que já existe.

| Camada | Arquivo | Pergunta que responde |
|---|---|---|
| Mapa | `INDEX.md` (um por pasta) | por onde entro? o que tem aqui? quando ler cada coisa? |
| Agora | `CURRENT.md` | o que está acontecendo? |
| Assunto | `topics/<slug>.md` | o que sabemos sobre X? |
| Dia | `daily/AAAA-MM-DD.md` | o que aconteceu naquele dia? |
| Bruto | mensagens, transcrições, código, PDFs | qual foi a palavra exata? |

Um projeto pode não ter todas. Um repositório de documentação costuma ter Mapa e Bruto, e as pastas fazem o papel de Assunto. Um assistente com memória de conversas costuma ter as cinco.

## 3. A escada de leitura (regra dura)

`INDEX → CURRENT → topic → daily → bruto`, nessa ordem, parando assim que a resposta for suficiente. Nunca carregar tudo.

Bruto só quando: há dúvida, há conflito entre fontes, a decisão é importante, ou é preciso citar a palavra exata.

## 4. Vários caminhos para a mesma coisa (regra dura)

No mínimo dois: **por tema** (as pastas) e **por tempo** ([TIMELINE.md](docs/TIMELINE.md)). Recomendado um terceiro: por pergunta (um registro de perguntas abertas) ou por pessoa (uma pasta por contato). Se um caminho falha, outro chega.

## 5. Procedência (regra dura)

Todo fato registrado carrega:

- **de onde veio:** `humano` · `agente` · `dedução` · `documento`
- **confiança:** alta · média · baixa
- **evidência:** link ou id do que sustenta

Dedução entra como baixa e não vira permanente sem confirmação.

## 6. Nada se apaga, tudo evolui (regra dura)

Fato novo aponta para o antigo: "substitui X em <data>, motivo: ...". Decisão rejeitada fica registrada com o motivo. Caminho que deu errado fica com o porquê.

## 7. Carimbo (regra dura para gerado; orientação para escrito à mão)

Todo arquivo gerado (`INDEX.md`, [TIMELINE.md](docs/TIMELINE.md)) e toda tabela de estado começa com `<!-- atlaz: gerado_em=DD/MM/AAAA fonte=<quem gerou> hash=<8 hex> -->`. O hash é do conteúdo que gerou o bloco: se mudou, o bloco está velho. A seção "Veja também" é marcada só pelos comentários de início e fim, sem hash: a ferramenta a refaz inteira a cada rodada. Arquivo escrito à mão não precisa de carimbo; o git é o histórico dele.

## 8. Modo cópia ou modo fonte (regra dura)

O projeto declara no `atlaz.json` (`"modo"`):

- **fonte:** o markdown é a verdade. Editar à mão é normal. Git é o histórico. (Exemplo: um repositório de documentação.)
- **cópia:** a verdade mora num banco; o markdown é gerado e regenerável. Editar à mão é proibido; apagar tudo e regenerar é operação normal. (Exemplo: um assistente que guarda a memória das conversas num banco.)

## 9. Ligação (regra dura)

- Links markdown relativos: `[Nome](caminho/relativo.md)`. Nunca `[[wikilink]]`: o Obsidian lê os dois, o resto do mundo só lê o primeiro.
- Todo arquivo aponta para o índice da pasta e é apontado por ele.
- Todo documento termina com "Veja também": para onde aponta, quem cita. Gerado.
- Ponta solta (arquivo que ninguém aponta) é aviso do lint.

## 10. Orçamento por camada (orientação)

Cada camada tem um tamanho máximo em linhas (`atlaz.json` → `orcamento`). Padrão: `INDEX.md` 120, `CURRENT.md` 80, outros 900. Passou, o lint avisa. Motivo: se o degrau de cima fica grande, o agente lê demais no lugar errado e a escada deixa de economizar.

## 11. Tabela de estado no topo (orientação)

Arquivos de registro (registro de decisões, de perguntas, de discordâncias) ganham no topo uma tabela gerada: id, título, estado, data. O agente lê a tabela e só desce para a entrada que interessa. Configurado em `atlaz.json` → `estado`.

## 12. Busca por palavra (orientação)

O jeito certo de chamar:

```
python ferramentas/atlaz.py . --buscar termo
python ferramentas/atlaz.py . --buscar "duas palavras"
```

A RAIZ (`.`) vem primeiro e o termo vem logo depois de `--buscar`. O termo nunca é a RAIZ: sem a RAIZ, vale a pasta atual (`atlaz.py --buscar termo` busca na pasta atual).

O termo é texto literal, sem diferença de maiúscula e minúscula. Usa `ripgrep` se existir (também no Windows), senão varre em Python; o resultado é o mesmo nos dois casos. Resultado ranqueado pela escada: ocorrência em `INDEX.md` vem antes de `CURRENT.md`, que vem antes de `topics/`, e assim por diante.

## 13. A ferramenta

`ferramentas/atlaz.py <raiz>` faz, nesta ordem: links relativos → `INDEX.md` por pasta → "Veja também" → [TIMELINE.md](docs/TIMELINE.md) → tabelas de estado → carimbos → lint. `--lint` só verifica: não escreve nada nem cria pasta. `--help` (ou `-h`) mostra o uso e sai sem escrever nada.

**Converge em até duas rodadas.** A primeira rodada pode criar um arquivo (um `INDEX.md` novo, a TIMELINE) que a segunda passa a citar. Da segunda em diante, no mesmo dia, rodar de novo não muda nada.

**O que entra no INDEX.** Cada pasta com `.md`, `.py` ou `.json` ganha o seu, mesmo sem nenhum `.md` (só código ou dado), e também cada pasta no caminho até ela. Cada `INDEX.md` lista os `.md`, `.py` e `.json` da pasta e as subpastas. Fica fora: pasta oculta (começa com `.`), pasta de `ignorar_pastas`, pasta de skill (com `SKILL.md`, que vira uma linha no índice de cima) e arquivo que o git ignora (é local, e o link quebraria em todo clone).

**Lint.** Erro (sai com código 1): link relativo quebrado, para `.md` ou para qualquer outro alvo (código, dado, imagem, pasta); acento trocado por "?" (fora de URL e do destino de link, onde "?" é normal). Aviso: órfão, nome duplicado, acima do orçamento.

**Uso errado.** Opção desconhecida (inclusive erro de grafia, como `--lnit`), mais de uma RAIZ, RAIZ que não é pasta, `--buscar` sem termo, `atlaz.json` inválido ou com caminho fora da RAIZ: sai com código 2, antes de escrever qualquer coisa. Uma falha inesperada (por exemplo, um `.md` fora de UTF-8) sai com 1.

**Só dentro da RAIZ (regra dura).** Nenhum caminho do `atlaz.json` pode sair da RAIZ (nem com `..`, nem absoluto). A ferramenta também não escreve num `.md` que é link simbólico para fora dela: avisa e segue.

**Saída.** Lida por pipe (agente, CI), sai em UTF-8 em qualquer sistema.

## 14. Configuração (`atlaz.json` na raiz)

```json
{
  "modo": "fonte",
  "entradas": ["README.md", "AGENTS.md"],
  "nao_tocar": ["transcricao-bruta.md"],
  "ignorar_pastas": [".git", "node_modules", ".venv"],
  "descricoes": {"CONSTITUTION.md": ["regras permanentes", "sempre no início"],
                 "scripts/relatorio.py": ["gera o relatório semanal", "antes de mudar o relatório"]},
  "pastas": {"docs/00-fundacao": "00 · Fundação"},
  "estado": ["docs/DECISION_LOG.md"],
  "indice_raiz": false,
  "orcamento": {"INDEX.md": 120, "*.md": 900},
  "timeline": {"arquivo": "docs/TIMELINE.md", "decisoes": "docs/DECISION_LOG.md",
               "registros": "", "discordancias": "", "sessoes_glob": ""}
}
```

Tudo opcional. Sem o arquivo, a ferramenta usa os padrões.

| Chave | O que faz | Padrão |
|---|---|---|
| `modo` | `fonte` ou `copia` (seção 8) | `fonte` |
| `entradas` | arquivos do topo da escada; nunca contam como órfãos | [README.md](README.md), [CLAUDE.md](CLAUDE.md), [AGENTS.md](AGENTS.md) |
| `nao_tocar` | arquivos que a ferramenta nunca reescreve | nenhum |
| `ignorar_pastas` | pastas que ficam fora de tudo | `.git`, `.obsidian`, `node_modules`, `__pycache__`, `.venv` |
| `descricoes` | "o que é" e "quando ler" de cada arquivo no INDEX | nenhuma |
| `pastas` | título do INDEX de cada pasta | o nome da pasta |
| `estado` | registros que ganham a tabela de estado no topo | nenhum |
| `indice_raiz` | gera `INDEX.md` também na raiz | `false` |
| `orcamento` | linhas máximas por camada (aviso) | seção 10 |
| `timeline` | de onde a TIMELINE tira os eventos; caminho vazio desliga a fonte | só o registro de decisões |

Em `descricoes`, a chave é o nome do arquivo ou o caminho relativo à raiz, e o caminho vence o nome. Serve para nomes repetidos em pastas diferentes (`__init__.py`, `relatorio.py`), que assim ganham descrições próprias.

**Formatos que a ferramenta reconhece** nos registros: decisões como `## ADR-NNN — Título` com uma linha `**Data:** DD/MM/AAAA`; registros como `### Registry #NNN — Título` com `**Origem:** ... DD/MM/AAAA`; discordâncias como `### DIS-NNN — DD/MM/AAAA`; sessões como `## Registro da sessão N — DD/MM/AAAA`, nos arquivos cujo caminho começa com `sessoes_glob`. Na tabela de estado, também valem títulos `## D-NNN — ...` e `## H-NNN — ...` (decisão e hipótese, em `##` ou `###`). O estado de cada entrada vem da linha `**Estado:**` (ou `**Status:**`).

## 15. O que o Atlaz não faz

- Não busca por significado (vetor). Ver "Futuro".
- Não decide o que é importante nem se um ramo vale abrir. Isso é trabalho de um modelo de decisão com confiança calibrada, outra peça.
- Não gera conteúdo. Só organiza e navega.

## 16. Futuro (só escrito, nada implementado)

| Ideia | O que seria | Depende de |
|---|---|---|
| Hábito | caminhos percorridos com frequência viram atalho no `INDEX.md` ("as 5 coisas mais procuradas") | uso real medido |
| Busca semântica local | modelo de embedding pequeno rodando na máquina; acha pela ideia, não pela palavra | instalar modelo; respeita a neutralidade porque é local e opcional |
| Poda com decisão calibrada | antes de abrir um ramo, perguntar "esse ramo tem o que procuro?" a um modelo de decisão; abre se incerto, pula se confiante que não | um modelo de decisão acessível ao agente por API |
| Estado, peso e hesitação | registrar em que estado uma coisa foi dita, quanto pesa (inegociável ou preferência) e onde havia dúvida | pesquisa em andamento |

<!-- atlaz:veja-tambem:inicio -->
## Veja também

Índice: [docs/INDEX.md](docs/INDEX.md)
Aponta para: [AGENTS.md](AGENTS.md) · [CLAUDE.md](CLAUDE.md) · [README.md](README.md) · [DECISION_LOG.md](docs/DECISION_LOG.md) · [TIMELINE.md](docs/TIMELINE.md)
Citado por: [AGENTS.md](AGENTS.md) · [README.md](README.md) · [ADOTAR.md](docs/ADOTAR.md)
_(seção gerado por atlaz.py; não editar à mão)_
<!-- atlaz:veja-tambem:fim -->
