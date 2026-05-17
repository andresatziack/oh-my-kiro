# Otimizacao de eficiencia da execucao do Ralph Loop

**Objetivo:** Reduzir o overhead fixo por iteracao do Ralph Loop (medido em ~17-24s/iteracao), aumentar estabilidade e manutenibilidade do codigo
**Não-Objetivos:** Mudar a arquitetura central do Ralph Loop (toda iteracao = nova session com context limpo); mudar como o CLI e invocado (session resume foi descartado pela pesquisa); mudar o sistema de hooks
**Arquitetura:** Cachear o resultado de detect_cli para evitar pings repetidos; precheck so roda uma vez; mesclar funcoes de prompt redundantes; corrigir posse de fd em pty_runner; simplificar a logica do heartbeat; modo claude recebe --no-session-persistence
**Tech Stack:** Python 3, pytest

## Tarefas

### Tarefa 1: cache do resultado de detect_cli()

**Arquivos:**
- Modify: `scripts/lib/cli_detect.py`
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
Em `test_ralph_loop.py`, adicione um teste: verifique que `detect_cli()` so e chamado uma vez no main loop (verificando no codigo-fonte que detect_cli e invocado fora do loop).

```python
def test_detect_cli_called_outside_loop():
    """detect_cli() must be called before the loop, not inside it."""
    source = open("scripts/ralph_loop.py").read()
    # Find the main loop: "for i in range(1, max_iterations + 1):"
    loop_start = source.index("for i in range(1, max_iterations + 1):")
    before_loop = source[:loop_start]
    in_loop = source[loop_start:]
    assert "detect_cli()" in before_loop, "detect_cli() should be called before the loop"
    assert "detect_cli()" not in in_loop, "detect_cli() should NOT be called inside the loop"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_detect_cli_called_outside_loop -v`
Expected: FAIL (detect_cli() is currently called inside the loop)

**Step 3: Write minimal implementation**
No `main()` de `ralph_loop.py`, mova a chamada de `detect_cli()` para fora do loop, armazene o resultado em uma variavel `base_cmd` e use essa variavel direto dentro do loop.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_detect_cli_called_outside_loop -v`
Expected: PASS

**Step 5: Commit**
`feat: cache detect_cli() result — save ~8s per iteration`

---

### Tarefa 2: precheck so roda uma vez

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
```python
def test_precheck_runs_only_once():
    """run_precheck should only appear in build_init_prompt, not build_prompt."""
    source = open("scripts/ralph_loop.py").read()
    # build_prompt should not call run_precheck at all
    build_prompt_body = source.split("def build_prompt(")[1].split("\ndef ")[0]
    assert "run_precheck" not in build_prompt_body, "build_prompt should not call run_precheck"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_precheck_runs_only_once -v`
Expected: FAIL (build_prompt currently calls run_precheck)

**Step 3: Write minimal implementation**
Modifique `build_prompt()`: remova a chamada `run_precheck()`; env_status fica sempre como "✅ Environment OK (cached)". precheck so e executado em `build_init_prompt()`.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_precheck_runs_only_once -v`
Expected: PASS

**Step 5: Commit**
`feat: precheck runs only on first iteration — save ~2s per subsequent iteration`

---

### Tarefa 3: mesclar build_prompt e build_init_prompt

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
```python
def test_single_build_prompt_function():
    """Only one prompt builder function should exist (merged)."""
    source = open("scripts/ralph_loop.py").read()
    assert "def build_init_prompt(" not in source, "build_init_prompt should be merged into build_prompt"
    assert "def build_prompt(" in source, "build_prompt should still exist"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_single_build_prompt_function -v`
Expected: FAIL (build_init_prompt still exists)

**Step 3: Write minimal implementation**
Mescle `build_init_prompt()` em `build_prompt()` adicionando o parametro `is_first: bool = False`. Atualize as chamadas em `main()`. **Tambem precisa atualizar** `test_init_prompt_differs_from_regular`: remover `from scripts.ralph_loop import build_init_prompt` e passar a chamar `build_prompt(is_first=True)` vs `build_prompt(is_first=False)`, validando a diferenca no texto "FIRST iteration".

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_single_build_prompt_function -v`
Expected: PASS

**Step 5: Commit**
`refactor: merge build_init_prompt into build_prompt — reduce 30 lines of duplication`

---

### Tarefa 4: corrigir posse de fd no pty_runner

**Arquivos:**
- Modify: `scripts/lib/pty_runner.py`
- Test: `tests/ralph-loop/test_pty_runner.py`

**Step 1: Write failing test**
```python
def test_master_fd_single_close(tmp_path):
    """master fd should only be closed once (by reader thread), not double-closed."""
    import scripts.lib.pty_runner as mod
    source = open(mod.__file__).read()
    # stop() should not close master — reader owns it
    stop_body = source.split("def stop():")[1].split("\n    return")[0]
    assert "os.close(master)" not in stop_body, "stop() should not close master fd — reader thread owns it"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_pty_runner.py::test_master_fd_single_close -v`
Expected: FAIL (stop() currently closes master)

**Step 3: Write minimal implementation**
Modifique `pty_run()`: remova `os.close(master)` de `stop()`, deixando a thread `_reader()` como dona exclusiva do fechamento do master fd.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_pty_runner.py::test_master_fd_single_close -v`
Expected: PASS

**Step 5: Commit**
`fix: pty_runner single fd ownership — eliminate double-close race`

---

### Tarefa 5: simplificar a logica do heartbeat

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
```python
def test_heartbeat_no_confusing_elapsed():
    """_heartbeat should not have the confusing elapsed calculation."""
    source = open("scripts/ralph_loop.py").read()
    assert "heartbeat_interval * (idle_elapsed // heartbeat_interval" not in source, \
        "Confusing elapsed calculation should be removed from _heartbeat"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_heartbeat_no_confusing_elapsed -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Simplifique `_heartbeat()`: remova a variavel `elapsed` e a logica de calculo confusa. O heartbeat so imprime `checked/total`; o idle watchdog so acompanha `idle_elapsed`.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_heartbeat_no_confusing_elapsed -v`
Expected: PASS

**Step 5: Commit**
`fix: simplify heartbeat — remove confusing elapsed calculation`

---

### Tarefa 6: modo claude com --no-session-persistence

**Arquivos:**
- Modify: `scripts/lib/cli_detect.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Step 1: Write failing test**
```python
def test_claude_cmd_has_no_session_persistence():
    """Claude command should include --no-session-persistence to avoid disk I/O."""
    from scripts.lib.cli_detect import detect_cli
    from unittest.mock import patch
    import subprocess
    with patch('shutil.which', side_effect=lambda x: '/usr/bin/claude' if x == 'claude' else None), \
         patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0, stdout='pong', stderr='')
        cmd = detect_cli()
        assert '--no-session-persistence' in cmd
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_claude_cmd_has_no_session_persistence -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Adicione `'--no-session-persistence'` ao retorno de `detect_cli()` quando o CLI for claude.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_claude_cmd_has_no_session_persistence -v`
Expected: PASS

**Step 5: Commit**
`feat: add --no-session-persistence to claude command — reduce disk I/O`

## Review

Round 1: Goal Alignment ✅ APPROVE | Verify Correctness ✅ APPROVE | Completeness ❌ REQUEST CHANGES (Task 3 breaks test import) | Performance ✅ APPROVE
→ Fixed: Task 3 Step 3 updated to explicitly update test_init_prompt_differs_from_regular
Round 2: Goal Alignment ✅ APPROVE | Verify Correctness ❌ REQUEST CHANGES (julgamento equivocado: rodaram os verify commands antes da implementacao)
→ Calibration: Verify Correctness finding discarded (expected pre-implementation state)

**Final Verdict: APPROVED**

## Checklist

- [x] detect_cli chamado fora do loop | `python3 -c "s=open('scripts/ralph_loop.py').read(); l=s.index('for i in range(1,'); print('PASS' if 'detect_cli()' not in s[l:] else 'FAIL')" | grep -q PASS`
- [x] precheck so roda na primeira iteracao | `python3 -c "s=open('scripts/ralph_loop.py').read(); b=s.split('def build_prompt(')[1].split('\ndef ')[0]; print('PASS' if 'run_precheck' not in b else 'FAIL')" | grep -q PASS`
- [x] build_init_prompt mesclado | `python3 -c "s=open('scripts/ralph_loop.py').read(); print('PASS' if 'def build_init_prompt(' not in s else 'FAIL')" | grep -q PASS`
- [x] pty_runner stop() nao fecha master fd | `python3 -c "s=open('scripts/lib/pty_runner.py').read(); stop=s.split('def stop():')[1].split('return')[0]; print('PASS' if 'os.close(master)' not in stop else 'FAIL')" | grep -q PASS`
- [x] heartbeat sem calculo confuso de elapsed | `python3 -c "s=open('scripts/ralph_loop.py').read(); print('PASS' if 'heartbeat_interval * (idle_elapsed' not in s else 'FAIL')" | grep -q PASS`
- [x] comando claude inclui --no-session-persistence | `python3 -c "s=open('scripts/lib/cli_detect.py').read(); print('PASS' if 'no-session-persistence' in s else 'FAIL')" | grep -q PASS`
- [x] testes de regressao passam | `python3 -m pytest tests/ralph-loop/ -v -m 'not slow'`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Reviewer Feedback (Round 1)

### Completeness reviewer - REQUEST CHANGES
**Finding:** Task 3 removes `build_init_prompt` but `test_init_prompt_differs_from_regular` (test_ralph_loop.py:442) imports it. Plan mentions updating the test but doesn't specify how.

**Resolution:** Task 3 Step 3 updated — the test must be rewritten to call `build_prompt(is_first=True)` vs `build_prompt(is_first=False)` and verify the "FIRST iteration" text difference. The import line `from scripts.ralph_loop import build_init_prompt` must be removed.
