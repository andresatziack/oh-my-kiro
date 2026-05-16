# Smoke Test de Dispatch Paralelo

**Objetivo:** Verify ralph_loop.py batch scheduler and parallel subagent dispatch work end-to-end.
**Não-Objetivos:** Not testing complex scenarios. Just a smoke test.
**Arquitetura:** 3 independent tasks (no file overlap) + 1 dependent task.
**Tech Stack:** Bash (touch files)

## Review
Smoke test — no review needed.

## Tarefas

### Tarefa 1: Create file alpha

**Arquivos:**
- Create: `/tmp/ralph-test-alpha.txt`

**Verificação:** `test -f /tmp/ralph-test-alpha.txt`

Create `/tmp/ralph-test-alpha.txt` with content "alpha".

---

### Tarefa 2: Create file beta

**Arquivos:**
- Create: `/tmp/ralph-test-beta.txt`

**Verificação:** `test -f /tmp/ralph-test-beta.txt`

Create `/tmp/ralph-test-beta.txt` with content "beta".

---

### Tarefa 3: Create file gamma

**Arquivos:**
- Create: `/tmp/ralph-test-gamma.txt`

**Verificação:** `test -f /tmp/ralph-test-gamma.txt`

Create `/tmp/ralph-test-gamma.txt` with content "gamma".

---

### Tarefa 4: Combine into result

**Arquivos:**
- Create: `/tmp/ralph-test-result.txt`
- Modify: `/tmp/ralph-test-alpha.txt`

**Verificação:** `test -f /tmp/ralph-test-result.txt`

Concatenate alpha + beta + gamma into `/tmp/ralph-test-result.txt`.

## Checklist
- [x] alpha file created | `test -f /tmp/ralph-test-alpha.txt`
- [x] beta file created | `test -f /tmp/ralph-test-beta.txt`
- [x] gamma file created | `test -f /tmp/ralph-test-gamma.txt`
- [x] result file created | `test -f /tmp/ralph-test-result.txt`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
