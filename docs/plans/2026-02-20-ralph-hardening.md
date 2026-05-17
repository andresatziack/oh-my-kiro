# Refatoracao e enrijecimento geral do Ralph Loop

**Objetivo:** Refatorar inteiramente ralph_loop.py e seus modulos lib, removendo riscos conhecidos (race conditions, processos orfaos, estado sujo, falha silenciosa) e melhorando qualidade e testabilidade do codigo.
**Não-Objetivos:** Sem mudanca no comportamento externo do ralph loop nem na CLI; sem mudanca no formato do plan; sem novas funcionalidades (como criacao de PR, execucao remota).
**Arquitetura:** Quebrar `main()` de ralph_loop.py em fases testaveis (config -> validate -> loop -> cleanup). LockFile passa a usar `fcntl.flock` para mutex de verdade. WorktreeManager corrige a logica de squash merge abort e ganha retry para operacoes git. Eliminar todo hack e caminho de falha silenciosa.
**Tech Stack:** Python 3.10+, fcntl, subprocess, threading, pytest

## Tarefas

### Tarefa 1: LockFile com fcntl.flock para mutex real

**Arquivos:**
- Modify: `scripts/lib/lock.py`
- Test: `tests/ralph-loop/test_lock.py`

**Step 1: Write failing test**
Adicionar tres testes: test_flock_mutual_exclusion, test_flock_release_allows_reacquire, test_flock_context_manager. Validar: dois processos nao podem segurar o lock ao mesmo tempo; apos release o lock pode ser readquirido; o context manager funciona.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_lock.py::test_flock_mutual_exclusion tests/ralph-loop/test_lock.py::test_flock_release_allows_reacquire tests/ralph-loop/test_lock.py::test_flock_context_manager -v`
Expected: FAIL (metodo try_acquire nao existe)

**Step 3: Implementacao minima**
Reescrever `scripts/lib/lock.py`:
- `acquire()`: abre o arquivo -> `fcntl.flock(fd, LOCK_EX)` -> grava o PID
- `try_acquire()`: `fcntl.flock(fd, LOCK_EX | LOCK_NB)` -> sucesso retorna True; `BlockingIOError` retorna False
- `release()`: `fcntl.flock(fd, LOCK_UN)` -> fecha o fd -> remove o arquivo. **Idempotente**: chamada repetida nao lanca excecao (signal handler + atexit + fim de main podem chamar 3 vezes; ver ralph_loop.py L74/L466/L608)
- `is_held_by_alive_process()`: manter por compatibilidade
- `__enter__`/`__exit__`: usar acquire/release

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_lock.py -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'refactor: LockFile uses fcntl.flock for true mutual exclusion'`

---

### Tarefa 2: corrigir estado sujo no merge do WorktreeManager

**Arquivos:**
- Modify: `scripts/lib/worktree.py`
- Test: `tests/ralph-loop/test_worktree.py`

**Step 1: Write failing test**
Adicionar test_merge_failure_leaves_clean_state: provocar conflito -> merge falha -> verificar que `git status --porcelain` esta vazio.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py::test_merge_failure_leaves_clean_state -v`
Expected: FAIL

**Step 3: Implementacao minima**
Editar o except do merge(): remover o `git merge --abort` invalido; manter apenas `git reset --hard HEAD`.

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'fix: worktree merge uses reset --hard instead of merge --abort for squash'`

---

### Tarefa 3: mecanismo de retry para operacoes git

**Arquivos:**
- Create: `scripts/lib/git_retry.py`
- Test: `tests/ralph-loop/test_git_retry.py`
- Modify: `scripts/lib/worktree.py`

**Step 1: Write failing test**
Adicionar test_git_run_succeeds_first_try, test_git_run_retries_on_lock, test_git_run_gives_up_after_max_retries, test_git_run_no_retry_on_non_lock_error.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_git_retry.py -v`
Expected: FAIL (modulo nao existe)

**Step 3: Implementacao minima**
Criar git_retry.py: funcao `git_run()` que faz retry de erros transientes (ex.: index.lock) ate 3 vezes com backoff exponencial.
Substituir as chamadas git nas posicoes abaixo por git_run:
- worktree.py - 3 chamadas com check=True (L21 create, L29 merge --squash, L38 commit)
- ralph_loop.py L398-399 git add + git commit (commit do checklist em run_parallel_batch; AST confirmou que so existem 2 chamadas)

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_git_retry.py tests/ralph-loop/test_worktree.py -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'feat: git_retry module with exponential backoff for transient lock errors'`

---

### Tarefa 4: extracao de verify command com fail-closed

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Adicionar test_extract_verify_cmd_missing_returns_false, test_extract_verify_cmd_inline, test_extract_verify_cmd_fenced.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_extract_verify_cmd_missing_returns_false -v`
Expected: FAIL

**Step 3: Implementacao minima**
Trocar o fallback de _extract_verify_cmd: de "echo 'no verify command found'" para "false".

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_extract_verify_cmd_missing_returns_false tests/ralph-loop/test_ralph_loop.py::test_extract_verify_cmd_inline tests/ralph-loop/test_ralph_loop.py::test_extract_verify_cmd_fenced -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'fix: _extract_verify_cmd returns false instead of silent pass'`

---

### Tarefa 5: eliminar o objeto fake plan em build_batch_prompt

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Adicionar test_build_batch_prompt_uses_real_plan: passar um PlanFile real e validar que o prompt contem o progress_path e o findings_path corretos.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_build_batch_prompt_uses_real_plan -v`
Expected: FAIL

**Step 3: Implementacao minima**
Alterar a assinatura de build_batch_prompt para incluir `plan: PlanFile = None`. Remover o hack `type('_plan', (), {})()`.
**Atualizar o callsite:** ralph_loop.py L547 `build_batch_prompt(batches[0], plan_path, i)` -> passar o plan tambem (AST confirmou que so existe esta chamada).

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_build_batch_prompt_uses_real_plan -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'refactor: build_batch_prompt accepts PlanFile, eliminates fake plan hack'`

---

### Tarefa 6: dividir main() em fases testaveis

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Adicionar test_parse_config_defaults, test_parse_config_from_argv, test_validate_plan_missing.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_parse_config_defaults -v`
Expected: FAIL

**Step 3: Implementacao minima**
Extrair de main() para parse_config(argv) -> Config dataclass, e validate_plan(plan_path) -> PlanFile. main() vira uma casca fina.

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_parse_config_defaults tests/ralph-loop/test_ralph_loop.py::test_parse_config_from_argv tests/ralph-loop/test_ralph_loop.py::test_validate_plan_missing -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'refactor: extract parse_config, validate_plan from main()'`

---

### Tarefa 7: cleanup_stale seguro - checar processos ativos

**Arquivos:**
- Modify: `scripts/lib/worktree.py`
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_worktree.py`

**Step 1: Write failing test**
Adicionar test_cleanup_stale_preserves_active_worktrees: criar worktree + .ralph-worker.lock (com PID atual) -> rodar cleanup_stale -> verificar que o worktree continua existindo.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py::test_cleanup_stale_preserves_active_worktrees -v`
Expected: FAIL

**Step 3: Implementacao minima**
Em cleanup_stale(): consultar o .ralph-worker.lock; se o PID estiver vivo, pula.
Em run_parallel_batch: ao criar o worktree, gravar o .ralph-worker.lock.

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'fix: cleanup_stale checks for active worker locks before removing'`

---

### Tarefa 8: signal handler thread-safe + cleanup handler robusto

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Adicionar test_cleanup_handler_with_empty_procs e test_cleanup_handler_with_dead_pids.

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_cleanup_handler_with_empty_procs tests/ralph-loop/test_ralph_loop.py::test_cleanup_handler_with_dead_pids -v`
Expected: precisa validar

**Step 3: Implementacao minima**
Em _cleanup_handler, criar um snapshot via list(child_procs) antes de iterar.

**Conserto extra:** ralph_loop.py L328 abre `open(log_path, "w")` sem `with`; em caso de Popen falhar ha vazamento de fd. Usar `with` ou try/finally (AST confirma que so existe este open cru).

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_cleanup_handler_with_empty_procs tests/ralph-loop/test_ralph_loop.py::test_cleanup_handler_with_dead_pids -v`
Expected: PASS

**Step 5: Commit**
`git commit -am 'fix: cleanup handler uses list snapshots for thread safety'`

---

### Tarefa 9: testes de integracao - mutex via flock + regressao completa

**Arquivos:**
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Adicionar test_flock_prevents_double_ralph: subir o primeiro ralph (sleep 60), subir o segundo -> verificar que o segundo retorna exit 1 e a saida contem "lock" ou "already running".

**Step 2: Run test - verificar que falha**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_flock_prevents_double_ralph -v`
Expected: FAIL

**Step 3: Implementacao minima**
Em main(), trocar `lock.acquire()` por `try_acquire()`; se falhar, `die("Another ralph-loop is already running")`.

**Step 4: Run test - verificar que passa**
Run: `python3 -m pytest tests/ralph-loop/ -v`
Expected: ALL PASS

**Step 5: Commit**
`git commit -am 'test: integration test for flock mutual exclusion + full regression'`

## Review
<!-- Reviewer writes here -->

## Checklist

- [x] LockFile usa fcntl.flock para mutex real | `grep -q "fcntl.flock" scripts/lib/lock.py && python3 -c "from scripts.lib.lock import LockFile; print('ok')"`
- [x] metodo try_acquire existe e e chamavel | `python3 -c "from scripts.lib.lock import LockFile; assert hasattr(LockFile, 'try_acquire'); print('ok')"`
- [x] dois processos nao podem segurar o lock simultaneamente | `python3 -m pytest tests/ralph-loop/test_lock.py::test_flock_mutual_exclusion -v`
- [x] apos falha de merge no worktree, o branch principal fica limpo | `python3 -m pytest tests/ralph-loop/test_worktree.py::test_merge_failure_leaves_clean_state -v`
- [x] modulo git_retry existe e pode ser importado | `python3 -c "from scripts.lib.git_retry import git_run; print('ok')"`
- [x] git_retry faz retry em erro de lock | `python3 -m pytest tests/ralph-loop/test_git_retry.py::test_git_run_retries_on_lock -v`
- [x] git_retry levanta excecao apos atingir max retries | `python3 -m pytest tests/ralph-loop/test_git_retry.py::test_git_run_gives_up_after_max_retries -v`
- [x] verify command ausente retorna false (fail-closed) | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_extract_verify_cmd_missing_returns_false -v`
- [x] build_batch_prompt aceita parametro PlanFile | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_build_batch_prompt_uses_real_plan -v`
- [x] funcao parse_config existe e retorna defaults corretos | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_parse_config_defaults -v`
- [x] validate_plan levanta SystemExit quando o arquivo nao existe | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_validate_plan_missing -v`
- [x] cleanup_stale preserva worktrees ativos | `python3 -m pytest tests/ralph-loop/test_worktree.py::test_cleanup_stale_preserves_active_worktrees -v`
- [x] cleanup handler com lista vazia nao quebra | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_cleanup_handler_with_empty_procs -v`
- [x] segunda instancia de ralph e bloqueada pelo lock | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_flock_prevents_double_ralph -v`
- [x] testes de regressao passam | `python3 -m pytest tests/ralph-loop/ -v`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
