# ADOTAR — como usar o Atlaz num projeto

## Em 4 passos

1. Copie `ferramentas/atlaz.py` para o projeto. É um arquivo só, sem dependências além do Python 3.7 ou mais novo.
2. Crie um `atlaz.json` na raiz (ver [SPEC, seção 14](../SPEC.md)). O mínimo é `{"modo": "fonte"}`.
3. Rode `python atlaz.py .` e corrija o que o lint apontar como erro.
4. Rode a ferramenta antes de todo commit: num hook do git, no CI ou no fim de cada sessão do agente.

## Qual modo escolher

| | Modo fonte | Modo cópia |
|---|---|---|
| Onde mora a verdade | no markdown | num banco de dados |
| Editar o `.md` à mão | normal | proibido: o markdown é regenerado |
| Camadas típicas | INDEX e bruto; as pastas fazem o papel de topics | todas: INDEX, CURRENT, topics, daily e bruto |
| Caminhos de acesso | por tema (pastas), por data (TIMELINE), por pergunta (um registro) | por pessoa (uma pasta por contato), por dia, por assunto |
| Procedência | nos registros de decisão (motivo e alternativas) | campos no banco: fonte, confiança e evidência |
| Quem gera a árvore | `atlaz.py` mantém índices, links, linha do tempo e lint | o próprio sistema gera a árvore a partir do banco; `atlaz.py` confere |
| Exemplo | um repositório de documentação | um assistente que guarda a memória das conversas num banco |

## Na CI

O lint sai com código 1 quando há erro (ou numa falha inesperada) e com 2 quando o uso está errado, inclusive com `atlaz.json` inválido. Um passo de CI basta:

```bash
python ferramentas/atlaz.py . --lint
```

## Ao mudar a convenção

Uma mudança só entra na SPEC quando serve a mais de um tipo de projeto. Se só um precisa, vira opção no `atlaz.json`. Registre a decisão no [DECISION_LOG.md](DECISION_LOG.md).

<!-- atlaz:veja-tambem:inicio -->
## Veja também

Índice desta pasta: [INDEX.md](INDEX.md)
Aponta para: [SPEC.md](../SPEC.md) · [DECISION_LOG.md](DECISION_LOG.md)
Citado por: [AGENTS.md](../AGENTS.md) · [README.md](../README.md)
_(seção gerado por atlaz.py; não editar à mão)_
<!-- atlaz:veja-tambem:fim -->
