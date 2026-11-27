# ORIGEM — de onde o Atlaz veio

Escrito como investigação, não como manual: o que aconteceu, na ordem.

## 1. A memória de um agente (agosto de 2026)

O Atlaz nasceu dentro da Iryx, organizando a memória de um agente de IA. Para o agente não carregar tudo toda vez, a memória virou uma árvore de arquivos (`INDEX`, `CURRENT`, `topics/`, `daily/`) e uma regra escrita: **"escada obrigatória de busca: INDEX → CURRENT → topic → daily → mensagens originais, parando assim que a resposta for suficiente."** Junto vieram a procedência por fato (fonte, confiança, evidência), o "fato novo não apaga o antigo" e o cabeçalho com data e hash em tudo que é gerado.

## 2. A mesma dor num repositório de documentação (setembro de 2026)

Um repositório de documentação da casa guardava regras sem motivo e documentos sem ligação. A mesma escada resolvia. Duas referências ajudaram a dar forma:

- **A analogia da cidade:** endereço, lógica, hábito (está no [README](../README.md)).
- **HNSW**, o algoritmo por trás de muitos bancos vetoriais: camadas com saltos largos em cima e ajuste fino embaixo. O Atlaz faz o mesmo com pastas e índices, sem vetor nenhum.

## 3. O nome e a regra (20/09/2026)

Uma tecnologia que aparece em mais de um projeto ganha nome e repositório próprios, com uma condição: **só quando dois projetos reais a usam**. Antes disso, o segundo uso ainda não mostrou onde fica a fronteira entre a tecnologia e o detalhe do projeto. A memória em camadas passou nessa regra. Nomes considerados: Escada, Trilha, Camadas, Atlas. O escolhido foi **Atlaz**, com Z.

## 4. A ferramenta (21 a 23/09/2026)

A especificação foi generalizada a partir desse primeiro uso, tirando o que era específico dele. A ferramenta foi reescrita para receber configuração (`atlaz.json`) e ganhou carimbo com hash, tabela de estado, busca ranqueada e orçamento por camada. Na v0.2, o uso em outro repositório revelou 11 defeitos, corrigidos aqui (ver [DECISION_LOG.md](DECISION_LOG.md), ADR-005).

## 5. Versão pública (novembro de 2026)

A v0.3 abriu o código. Os padrões da ferramenta ficaram genéricos, a ferramenta passou a recusar escrever fora da pasta do projeto e a documentação deixou de citar projetos internos (ADR-006).

## Referências

- HNSW: Malkov e Yashunin, "Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs" (2016).

<!-- atlaz:veja-tambem:inicio -->
## Veja também

Índice desta pasta: [INDEX.md](INDEX.md)
Aponta para: [README.md](../README.md) · [DECISION_LOG.md](DECISION_LOG.md)
Citado por: [AGENTS.md](../AGENTS.md) · [README.md](../README.md)
_(seção gerado por atlaz.py; não editar à mão)_
<!-- atlaz:veja-tambem:fim -->
