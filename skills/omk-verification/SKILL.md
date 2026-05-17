---
name: omk-verification
description: "Evidence before claims — run verification commands before any completion/success statement. Trigger when about to claim 'done', 'fixed', 'passing', 'complete', 'works now', before committing, creating PRs, or moving to next task. Also trigger when expressing satisfaction like 'great', 'perfect', or any positive assessment of work state without fresh evidence."
---

## Trigger Examples
- "我觉得改好了" → 先跑验证
- "tests should pass now" → 先跑验证
- "准备提 PR 了" → 先跑验证
- "this fix looks correct" → 先跑验证
- "done, moving to next task" → 先跑验证

# Verificação antes da conclusão

## Visão geral

Reivindicar que o trabalho está concluído sem verificar é desonestidade, não eficiência.

**Princípio central:** Evidência antes da reivindicação, sempre.

**Violar a letra desta regra é violar o espírito desta regra.**

## A Lei de Ferro

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

Se você não rodou o comando de verificação nesta mensagem, não pode reivindicar que ele passa.

## A função-Gate

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Falhas comuns

| Reivindicação | Requer | Não é suficiente |
|-------|----------|----------------|
| Tests pass | Saída do test command: 0 falhas | Run anterior, "should pass" |
| Linter clean | Saída do linter: 0 erros | Verificação parcial, extrapolação |
| Build succeeds | Build command: exit 0 | Linter passando, "logs look good" |
| Bug fixed | Testar o sintoma original: passa | Código mudou, assumido como fixed |
| Regression test works | Ciclo red-green verificado | Teste passa uma vez |
| Agent completed | Diff do VCS mostra alterações | Agent reportou "success" |
| Requirements met | Checklist linha a linha | Tests passing |

## Sinais de alerta - PARE

- Usar "should", "probably", "seems to"
- Expressar satisfação antes de verificar ("Great!", "Perfect!", "Done!", etc.)
- Prestes a commit/push/PR sem verificar
- Confiar em relatórios de sucesso de agents
- Apoiar-se em verificação parcial
- Pensar "just this once"
- Cansado e querendo encerrar
- **QUALQUER frase que implique sucesso sem ter rodado a verificação**

## Prevenção de racionalizações

| Desculpa | Realidade |
|--------|---------|
| "Should work now" | RODE a verificação |
| "I'm confident" | Confiança ≠ evidência |
| "Just this once" | Sem exceções |
| "Linter passed" | Linter ≠ compilador |
| "Agent said success" | Verifique de forma independente |
| "I'm tired" | Cansaço ≠ desculpa |
| "Partial check is enough" | Parcial não prova nada |
| "Different words so rule doesn't apply" | Espírito sobre letra |

## Padrões-chave

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Delegação para agent:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## Por que isso importa

De 24 falhas registradas:
- O human partner disse "I don't believe you", confiança quebrada
- Funções não definidas foram para produção, iam crashar
- Requirements faltando foram para produção, features incompletas
- Tempo perdido em conclusão falsa → redirect → retrabalho
- Viola: "Honesty is a core value. If you lie, you'll be replaced."

## Quando aplicar

**SEMPRE antes de:**
- QUALQUER variação de reivindicação de sucesso/conclusão
- QUALQUER expressão de satisfação
- QUALQUER afirmação positiva sobre o estado do trabalho
- Commitar, criar PR, concluir task
- Avançar para a próxima task
- Delegar para agents

**A regra se aplica a:**
- Frases exatas
- Paráfrases e sinônimos
- Implicações de sucesso
- QUALQUER comunicação que sugira conclusão/correção

## A linha final

**Sem atalhos para a verificação.**

Rode o comando. Leia a saída. ENTÃO declare o resultado.

Isso é não negociável.
