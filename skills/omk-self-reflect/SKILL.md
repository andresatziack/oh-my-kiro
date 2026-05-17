---
name: omk-self-reflect
description: "Agent self-learning: promote recurring episodes to rules, capture complex corrections. Trigger when hook outputs 🔥 or ⬆️ (promotion needed), 🚨 (complex correction), or when user says 'reflect', 'learn from this', 'remember this', 'always do X', 'never do Y', '@reflect'. Also trigger when same mistake pattern appears ≥3 times in episodes."
---

## Trigger Examples
- "lembre disso, sempre fazer assim daqui pra frente"
- "always use jq for JSON, never sed"
- "@reflect consolide essa licao aprendida"
- "I told you this before, capture it"
- "esse erro ja se repetiu varias vezes, vira regra"

# Self-Reflect - Sistema de auto-aprendizagem do agent

## Escopo (v3)

1. **Execução de promoção**: Quando o hook gera 🔥 ou ⬆️, leia episodes.md,
   destile em uma rule de 1 a 2 linhas, proponha ao usuário e escreva em rules.md se aprovado.
   Marque os episodes de origem como `promoted`.

2. **Captura de insight complexo**: Quando o hook gera 🚨 (complexo) e a correção
   é muito complexa para captura automática (sem padrão simples DO/DON'T), ajude o usuário
   a articular e escrever em episodes.md no mesmo formato.

NÃO é responsável por: captura diária (o hook faz), dedup (o hook faz),
relatório de qualidade (o hook faz).

## Alvos de sincronização

| Cenário | Alvo |
|----------|--------|
| Princípio de topo (aprovado pelo usuário) | AGENTS.md / CLAUDE.md (seção Principles) |
| Promoção (≥3 do mesmo padrão) | knowledge/rules.md (seção de keyword correspondente) |
| Insight complexo | knowledge/episodes.md |
| Regra aplicável por código | .kiro/rules/enforcement.md |

## Escrevendo em arquivos protegidos (AGENTS.md / CLAUDE.md / .claude/rules/)

Quando o usuário aprovar explicitamente escrever em um arquivo protegido de instrução, o agent DEVE executar autonomamente o fluxo de três steps, NÃO espere o humano fazer manualmente:
1. `touch .skip-instruction-guard`
2. Escreva a alteração
3. `rm -f .skip-instruction-guard`

Isso ignora o pre-write hook temporariamente. Faça isso somente quando o usuário aprovou claramente o conteúdo na conversa atual.

## Formato de Episode

`DATE | STATUS | KEYWORDS | SUMMARY`

- DATE: YYYY-MM-DD
- STATUS: active / resolved / promoted
- KEYWORDS: 1 a 3 termos técnicos em inglês, ≥4 chars, separados por vírgula
- SUMMARY: ≤80 chars, sem o caractere `|`, DO/DON'T acionável

## Processo de promoção

1. Leia episodes.md, encontre keywords que apareçam ≥3 vezes em episodes ativos
2. Destile em uma rule de 1 a 2 linhas com DO/DON'T + cenário-trigger
3. Leia os headers de seção em knowledge/rules.md (`## [keywords]`)
4. **Clusterização**, escolha a seção alvo por correspondência semântica:
   - Compare as keywords do episode com a lista de keywords de cada seção
   - Escolha a seção com maior sobreposição de keywords + relevância semântica
   - Se nenhuma seção corresponder → crie uma nova seção `## [episode-keywords]` no fim do arquivo
   - Se for inserir em uma seção existente → anexe novas keywords no header da seção, se agregam valor
5. Proponha ao usuário para aprovação (mostre a seção alvo)
6. Se aprovado: anexe a rule à seção escolhida e mude o status dos episodes de origem para `promoted`
7. Saída: ⬆️ Promoted to rules.md [section]: 'RULE'

Nota: episodes promovidos são auto-limpos pelo context-enrichment no próximo início de sessão.

## Padrões-trigger

**Alta confiança (90%)**:
- `remember:` / `always:`
- `don't ... unless`
- `I told you`

**Média confiança (80%)**:
- `no, use X` / `not X, use Y`
- `you missed` / `why didn't you`

### Padrões de exclusão (não capturar)
- Perguntas terminadas com `?`
- Pedidos começando com `please` / `help me`
- Mensagens com mais de 300 caracteres sem padrão claro de DO/DON'T

## Ao detectar

1. Confirme: `📝 Learning captured: '[preview]'`
2. **Escreva no arquivo alvo imediatamente** (sem fila)
3. Continue respondendo à pergunta do usuário
