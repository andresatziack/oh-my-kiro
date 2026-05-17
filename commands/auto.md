Você DEVE seguir esta sequência exata. @auto é um pipeline totalmente automatizado, sem confirmação do usuário entre estágios, exceto durante as perguntas de Expansão.

## Estágio 1: Expansão (Phase 0 + Readiness Check)

Siga `skills/omk-planning/SKILL.md` Phase 0 incluindo o **Step 6: Readiness Check**.

- Execute o checklist de 4 dimensões (Goal / Constraints / Success Criteria / Context)
- Se alguma dimensão estiver ❌, faça UMA pergunta ao usuário (com Challenge Modes a partir da 2ª pergunta)
- Quando todas as dimensões estiverem ✅, gere um resumo de um parágrafo descrevendo o entendimento validado
- `touch .brainstorm-confirmed`

Diferença em relação a @plan: @plan aguarda confirmação explícita do usuário após Phase 0. @auto prossegue automaticamente assim que o Readiness Check passa.

## Estágio 2: Planejamento (Phase 1)

Leia `skills/omk-planning/SKILL.md` Phase 1. Escreva o plan em `docs/plans/<date>-<slug>.md` com Goal, Tasks (estrutura TDD), `## Review` e `## Checklist` com comandos de verify.

Siga todas as Checklist Structure Rules de `commands/plan.md` Step 2.

## Estágio 3: Review (Phase 1.5 + Pre-mortem)

Siga `skills/omk-planning/SKILL.md` Phase 1.5:
1. Execute a **Pre-mortem Analysis**, identificando 3 riscos de falha (Integration / Assumption / Environment)
2. Selecione os ângulos de review (2 fixos + 2 aleatórios = 4 reviewers)
3. Dispare 4 subagents reviewers em paralelo com as perguntas do pre-mortem injetadas

**Como lidar com REQUEST CHANGES:**
- @auto revisa o plan autonomamente com base no feedback dos reviewers (máximo 2 rodadas de revisão)
- Após cada revisão, dispare novamente os reviewers para as seções alteradas
- Se ainda houver REQUEST CHANGES após 2 rodadas: **PARE** e diga ao usuário o que continua sem resolução. O usuário precisa intervir manualmente.

## Estágio 4: Execução

Depois que todos os reviewers derem APPROVE (ou após o usuário resolver os pontos pendentes):
1. Escreva o caminho do plan em `docs/plans/.active`
2. `unlink .brainstorm-confirmed 2>/dev/null || true`
3. Faça commit automático dos artefatos do plan (apenas caminhos de arquivo explícitos, nunca `git add -A`)
4. Execute `@execute` para iniciar a execução das tasks

## Estágio 5: Conclusão

Quando a execução terminar:
- Reporte o status final (itens concluídos / pendentes / pulados)
- Se houver itens pendentes, resuma o que falhou e sugira próximos passos
- Limpe `.active` se todos os itens estiverem concluídos

---
User's requirement:
(A próxima mensagem do usuário é o requisito. Se esta for a primeira mensagem após @auto ter sido invocado e nenhum requisito aparecer acima, aguarde a próxima mensagem do usuário, ela conterá o requisito. NÃO pergunte "o que você quer fazer?", o usuário já sabe que precisa fornecer a entrada após @auto.)
