---
name: omk-agent
description: "Distill a top-level principle into knowledge/rules.md. Trigger when user says 'add rule', 'new principle', 'enforce this', '@agent', or wants to codify an architectural decision, workflow principle, or behavioral guideline into persistent rules."
argument-hint: "[principle to capture]"
disable-model-invocation: true
---

## Trigger Examples
- "@agent 所有 JSON 操作必须用 jq"
- "add this as a permanent rule"
- "enforce: never skip tests"
- "把这个原则写进规则"
- "@agent submodule 修改必须走 worktree"

# Agent - Distilar princípio de topo

Captura um princípio em knowledge/rules.md como uma regra preparada (staged).

## Input
$ARGUMENTS

## Processo
1. Se nenhum input for fornecido, pergunte ao usuário: "What principle should I capture?"
2. Extraia: cenário-trigger + ação DO/DON'T + keywords
3. Verifique deduplicação: grep -iw keywords em knowledge/rules.md e knowledge/episodes.md
   - Já em rules → avise o usuário, pule
   - Já em episodes com mesmo significado → avise o usuário, sugira upgrade para rule
4. Determine a severidade: 🔴 (crítica, sempre injetada) ou 🟡 (relevante, casada por keyword)
5. Encontre ou crie um header de seção `## [keyword1,keyword2]` correspondente em knowledge/rules.md
6. Anexe a rule sob essa seção, formato: `🔴 N. SUMMARY` ou `🟡 N. SUMMARY`
7. Cap: máximo 5 rules por seção, máximo 30 rules no total. Avise se estiver perto do limite.
8. Saída: 📝 Captured → rules.md: 'SUMMARY'

## Regras
- O summary deve conter um DO/DON'T acionável, não narrativa
- Keywords: 1 a 3 termos técnicos em inglês, ≥ 4 chars cada, separados por vírgula
- Severidade padrão: 🟡 (use 🔴 apenas para princípios que devem se aplicar a TODA conversa)
