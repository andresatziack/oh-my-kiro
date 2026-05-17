# Verify-completion como restricao forte do Ralph Loop

**Objetivo:** Promover verify-completion de L3 advisory (~50% de aderencia) para restricao forte; aproveitar o loop bash externo do Ralph Loop: se o agent parou nao tem problema, enquanto a checklist nao estiver toda marcada, sobe uma instancia nova para continuar.

**Arquitetura:** O comando `@execute` invoca o script bash `ralph-loop.sh`; o script roda em loop instancias do Kiro CLI executando os itens da checklist do plan, com context fresco a cada iteracao, ate todos os itens estarem marcados.

**Tech Stack:** Bash + Kiro CLI (`--no-interactive --trust-all-tools`)

## Tarefas

### Tarefa 1: reescrever `commands/execute.md`

**Arquivos:**
- Modify: `commands/execute.md`

Mudar para:
1. Ler `docs/plans/.active` para localizar o arquivo do plan
2. Validar que o plan tem `## Checklist` com pelo menos um `- [ ]`
3. Executar `./scripts/ralph-loop.sh`
4. Apos o script encerrar, reportar o resultado e disparar a finishing skill

### Tarefa 2: reescrever `scripts/ralph-loop.sh`

**Arquivos:**
- Modify: `scripts/ralph-loop.sh`

**Template de prompt para a instancia interna do Kiro:**
```
You are executing a plan. Read the plan file at {PLAN_FILE}.
Find the next unchecked item (- [ ]) in the ## Checklist section.
Implement that ONE item. Verify it works (run tests/typecheck).
Then update the plan file: change that item from - [ ] to - [x].
Commit with message: feat: {item description}.
Then find the next - [ ] item and repeat. Do NOT stop while unchecked items remain.
If stuck after 3 attempts on one item, change it to - [SKIP] with reason, move to next.
```

**Estrategia de tratamento de erro:**
- Instancia Kiro com exit nao zero -> registra log e segue para a proxima iteracao (recuperavel)
- Arquivo do plan inexistente ou removido -> sai imediatamente (fatal)
- 3 iteracoes consecutivas sem mudanca na checklist (nenhum `- [x]` novo) -> sai e reporta travamento (circuit breaker)

**Tratamento de conflito Git:**
- No inicio de cada iteracao, checa `git status --porcelain`; se houver mudancas nao commitadas, faz `git stash` primeiro
- Conflito de merge nao e tratado (fora do escopo, precisa de intervencao humana)

### Tarefa 3: confirmar compatibilidade de `verify-completion.sh`

**Arquivos:**
- Verify: `hooks/feedback/verify-completion.sh`

Ja usa `find_active_plan()` para ler o ponteiro `.active`, compativel com o novo fluxo. Atua como camada advisory complementar.

## Checklist
- [x] `commands/execute.md` agora chama ralph-loop.sh em vez de executar tarefas sozinho
- [x] `scripts/ralph-loop.sh` usa o template de prompt indicado para subir instancias internas do Kiro, evitando recursao
- [x] `scripts/ralph-loop.sh` tem circuit breaker (3 iteracoes consecutivas sem progresso encerram a execucao)
- [x] `verify-completion.sh` e compativel com o ponteiro .active (confirmado, sem alteracoes)

## Review (Round 1)

~~**Verdict:** REQUEST CHANGES~~

Required fixes (resolvidos):
1. ~~Specify exact prompt template~~ -> Task 2 ja inclui o template de prompt completo
2. ~~Add error handling strategy~~ -> Task 2 ja inclui tratamento de erro em tres niveis
3. ~~Define timeout mechanism~~ -> circuit breaker: 3 iteracoes consecutivas sem progresso encerram a execucao
4. ~~Add git conflict resolution strategy~~ -> stash no inicio de cada iteracao; merge conflict requer intervencao humana

## Review (Round 2)

**Veredito:** APPROVE

All Round 1 fixes addressed:
1. ✅ Prompt template - complete and actionable
2. ✅ Error handling - three-level strategy (recoverable/fatal/circuit breaker)
3. ✅ Timeout - circuit breaker: 3 rounds no progress → exit
4. ✅ Git conflict - stash before each round, merge conflicts need human
