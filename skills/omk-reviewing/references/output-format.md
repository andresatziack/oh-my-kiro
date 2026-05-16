# Formato de Saída do Review

## Estrutura

```markdown
## Code Review Summary

**Files reviewed**: X files, Y lines changed
**Overall assessment**: [APPROVE / REQUEST_CHANGES / COMMENT]

---

## Findings

### P0 - Critical
(none or list)

### P1 - High
- **[file:line]** Brief title
  - Description of issue
  - Suggested fix

### P2 - Medium
...

### P3 - Low
...

---

## Removal/Iteration Plan
(if applicable)

## Additional Suggestions
(optional improvements, not blocking)
```

## Comentários inline

Use este formato para findings específicos de arquivo:
```
::code-comment{file="path/to/file.ts" line="42" severity="P1"}
Description of the issue and suggested fix.
::
```

## Declaração de review limpo

Se nenhum issue for encontrado, declare explicitamente:
- O que foi verificado
- Quaisquer áreas não cobertas (por exemplo, "Did not verify database migrations")
- Riscos residuais ou testes de follow-up recomendados

## Confirmação de próximos passos

Após apresentar findings, pergunte ao usuário como prosseguir:

```markdown
---

## Next Steps

I found X issues (P0: _, P1: _, P2: _, P3: _).

**How would you like to proceed?**

1. **Fix all** - I'll implement all suggested fixes
2. **Fix P0/P1 only** - Address critical and high priority issues
3. **Fix specific items** - Tell me which issues to fix
4. **No changes** - Review complete, no implementation needed

Please choose an option or provide specific instructions.
```

**Importante**: NÃO implemente alterações até o usuário confirmar explicitamente. Este é um workflow review-first.
