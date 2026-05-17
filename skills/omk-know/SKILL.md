---
name: omk-know
description: "Capture knowledge into episodes.md. Trigger when user says 'remember', 'capture this', 'lesson learned', 'note this', '@know', or when preserving insights, corrections, or discoveries from the current conversation."
argument-hint: "[insight to capture]"
disable-model-invocation: true
---

## Trigger Examples
- "@know macOS stat 用 -f 不用 -c"
- "记一下这个坑"
- "capture this lesson"
- "note: this API requires auth header"
- "@know HubSpot API 有 rate limit 100/10s"

# Know - Captura de conhecimento

Lê a conversa atual e captura um insight em knowledge/episodes.md.

## Input
$ARGUMENTS

## Processo
1. Se nenhum input for fornecido, pergunte ao usuário: "What insight should I capture?"
2. Extraia: cenário-trigger + ação DO/DON'T + keywords
3. Verifique deduplicação: grep -iw keywords em knowledge/rules.md e knowledge/episodes.md
   - Já em rules → avise o usuário, pule
   - Já em episodes → avise o usuário com a contagem, sugira promoção se ≥ 3
4. Formato: `DATE | active | KEYWORDS | SUMMARY` (≤ 80 chars, sem | no summary)
5. Anexe em knowledge/episodes.md
6. Saída: 📝 Captured → episodes.md: 'SUMMARY'

## Regras
- O summary deve conter um DO/DON'T acionável, não narrativa
- Keywords: 1 a 3 termos técnicos em inglês, ≥ 4 chars cada, separados por vírgula
- Se episodes.md tiver ≥ 30 entradas, avise o usuário para limpar antes
