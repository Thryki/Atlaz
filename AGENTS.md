# AGENTS.md — como um agente de IA trabalha neste repositório

Antes de responder qualquer coisa:

1. Leia o [README.md](README.md) e a [SPEC.md](SPEC.md).
2. Leia o [docs/DECISION_LOG.md](docs/DECISION_LOG.md): o que já foi decidido e por quê.
3. Use a escada: índice antes de arquivo inteiro; pare quando tiver o suficiente.

## Regras

- **Entenda antes de mudar.** Leia, confira o impacto, proponha, e só então mude.
- **Uma decisão estrutural por vez.**
- **Toda decisão vai para o Decision Log**, com motivo e alternativas rejeitadas.
- **A ferramenta é a única que edita o que ela gera** (índices, "Veja também", tabelas de estado, linha do tempo). Nunca à mão.
- **Neutralidade:** o Atlaz precisa funcionar em qualquer editor e com qualquer agente. Nada de recurso que só uma ferramenta lê.
- **Regra de mudança:** uma mudança na convenção só entra na SPEC quando serve a mais de um tipo de projeto. Se só um precisa, vira opção no `atlaz.json`.
- **Casa de ferreiro:** este repositório é organizado pelo próprio Atlaz. Rode `python ferramentas/atlaz.py .` antes de todo commit. Lint vermelho não vai para o commit.
- Linguagem simples, em português. Marque a confiança: ✅ certeza com base ou 🎲 chute educado.

## Onde as coisas ficam

| Quero... | Vá para |
|---|---|
| as regras | [SPEC.md](SPEC.md) |
| por que existe e de onde veio | [docs/ORIGEM.md](docs/ORIGEM.md) |
| como adotar num projeto | [docs/ADOTAR.md](docs/ADOTAR.md) |
| decisões | [docs/DECISION_LOG.md](docs/DECISION_LOG.md) |
| a ferramenta | [ferramentas/atlaz.py](ferramentas/atlaz.py) |
| um exemplo | [exemplos/modo-fonte/](exemplos/modo-fonte/INDEX.md) |
