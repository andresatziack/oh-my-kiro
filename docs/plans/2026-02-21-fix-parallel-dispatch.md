# Corrigir Bugs de Dispatch Paralelo do Ralph Loop

**Objetivo:** corrigir os 2 bugs centrais da execucao paralela do ralph loop: (1) tarefas ja concluidas sao reagendadas (o fallback de unchecked_tasks retorna todas as tarefas), (2) o merge vazio de um worker sem alteracoes e tratado como conflito e desperdica iteracoes.
**Não-Objetivos:** nao alterar o algoritmo do scheduler; nao alterar a estrategia de isolamento por worktree; nao adicionar novas funcionalidades.
**Arquitetura:** modificar `unchecked_tasks()` em plan.py e `merge()` em worktree.py. Todas as mudancas sao retrocompativeis.
**Tech Stack:** Python 3, pytest

## Tarefas

### Tarefa 1: Fix unchecked_tasks() unmatched fallback

Quando um item de checklist (como "testes de regressao passam") nao casa com nenhuma tarefa, o fallback atual retorna todas as tarefas. Isso faz com que tarefas ja concluidas sejam reagendadas repetidamente.

**Arquivos:**
- Modify: `scripts/lib/plan.py`
- Test: `tests/ralph-loop/test_plan.py`

**Step 1: Write failing test**

```python
# tests/ralph-loop/test_plan.py — append
def test_unchecked_tasks_skips_completed_with_unmatched_items(tmp_path):
    """When unmatched checklist items exist but all tasks are done, return empty."""
    plan_file = tmp_path / "plan.md"
    plan_file.write_text("""# Plan
## Tasks
### Task 1: Fix parser
Files: a.py
### Task 2: Fix lexer
Files: b.py
## Checklist
- [x] parser fixed | `echo ok`
- [x] lexer fixed | `echo ok`
- [x] 回归测试通过 | `python3 -m pytest tests/ -v`
- [x] 全量测试通过 | `python3 -m pytest tests/ -v`
""")
    from scripts.lib.plan import PlanFile
    p = PlanFile(plan_file)
    result = p.unchecked_tasks()
    # Should NOT return Task 1 and Task 2 — they're done
    assert len(result) == 0, f"Expected 0 tasks, got {[t.name for t in result]}"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks_skips_completed_with_unmatched_items -v`
Expected: FAIL (returns all 2 tasks due to unmatched fallback)

**Step 3: Write minimal implementation**

Modificar a logica de fallback de unmatched de `unchecked_tasks()` (~L90): quando houver itens unmatched unchecked, parar de retornar todas as tarefas e retornar apenas as tarefas que tem itens matched unchecked proprios. Se nenhuma tarefa tiver itens matched unchecked, retornar lista vazia.

```python
# Replace:
if unmatched_unchecked:
    return tasks
# With:
# Unmatched items don't cause all tasks to be returned.
# Only return tasks that have their own unchecked matched items.
```

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_plan.py -v`
Expected: PASS

**Step 5: Commit**

**Verificação:** `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks_skips_completed_with_unmatched_items -v`

### Tarefa 2: Handle empty squash merge gracefully

Quando um worker nao gera novos commits no worktree (tarefa ja concluida ou worker sem alteracoes), `git merge --squash` reporta "nothing to squash", `git commit` falha por ausencia de staged changes, e o merge inteiro e tratado como conflito.

**Arquivos:**
- Modify: `scripts/lib/worktree.py`
- Test: `tests/ralph-loop/test_worktree.py`

**Step 1: Write failing test**

```python
# tests/ralph-loop/test_worktree.py — append
def test_merge_no_changes_returns_true(git_repo):
    """merge() should return True (not False) when worker made no changes."""
    wm = WorktreeManager(base_dir=str(git_repo / ".worktrees"), project_root=str(git_repo))
    wm.create("empty")
    # Don't make any changes in the worktree
    result = wm.merge("empty")
    assert result is True, "Empty merge should succeed, not be treated as conflict"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py::test_merge_no_changes_returns_true -v`
Expected: FAIL (CalledProcessError from git commit with nothing to commit)

**Step 3: Write minimal implementation**

Modificar o metodo `merge()` em `worktree.py` (L26-48): apos `git merge --squash` e antes de `git commit`, verificar se ha staged changes. Se nao houver, pular o commit e retornar True.

```python
# After git merge --squash and git restore docs/plans/:
# Check if there are staged changes to commit
diff = subprocess.run(["git", "diff", "--cached", "--quiet"],
                      cwd=self.project_root, capture_output=True)
if diff.returncode == 0:
    # Nothing staged — worker made no changes, skip commit
    return True
git_run(["git", "commit", "-m", f"squash: merge {branch_name}"], ...)
```

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_worktree.py -v`
Expected: PASS

**Step 5: Commit**

**Verificação:** `python3 -m pytest tests/ralph-loop/test_worktree.py::test_merge_no_changes_returns_true -v`

## Checklist

- [x] unchecked_tasks nao retorna tarefas concluidas | `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks_skips_completed_with_unmatched_items -v`
- [x] merge vazio retorna True em vez de conflito | `python3 -m pytest tests/ralph-loop/test_worktree.py::test_merge_no_changes_returns_true -v`
- [x] testes de regressao passam | `python3 -m pytest tests/ralph-loop/ -v`
- [x] suite completa de testes passa | `python3 -m pytest tests/ -v`

## Review
<!-- Reviewer writes here -->

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
