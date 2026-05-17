# Execução Paralela Determinística do Ralph Loop

**Objetivo:** (1) Make ralph_loop.py deterministically analyze task dependencies and generate batch-aware prompts so kiro-cli reliably dispatches executor subagents in parallel. (2) Improve plan review quality by restructuring reviewer angles, dispatch queries, and calibration rules so all 4 parallel reviewers produce actionable findings.
**Não-Objetivos:** Not implementing multi-kiro-cli-instance parallelism (Strategy A). Not changing executor.json capabilities. Not modifying the plan file format. Not changing reviewer agent's tools/hooks.
**Arquitetura:** Two workstreams: (A) Parallel execution - add task dependency analysis to `scripts/lib/plan.py`, batch scheduler to `scripts/lib/scheduler.py`, batch-aware prompts to `ralph_loop.py`. (B) Review quality - restructure plan review angles in `skills/planning/SKILL.md` (from open-ended to analysis-method-bound), add structured dispatch query template, fix reviewer prompt contradictions, add executor model context.
**Tech Stack:** Python 3.10+ (re, pathlib, dataclasses), Markdown (skill/prompt files)

## Review

### Round 1 (Completeness / Testability / Technical Feasibility / Clarity)
- **Completeness**: REQUEST CHANGES — 6 findings. Calibrated: 5/6 rejected (transitive imports out of scope, file existence irrelevant to overlap check, rollback already addressed, no cycles in symmetric overlap, recomputation uses declared files not filesystem). 1 nit (malformed header handling — graceful degradation via fallback already covers this).
- **Testability**: REQUEST CHANGES — 4 findings. Accepted 2: added `test_unchecked_tasks_non_contiguous` for positional mapping edge case; strengthened dispatch prompt test to check for "agent_name"/"use_subagent". Rejected 2: batch recomputation mock too complex for marginal value; fallback mock unnecessary since crash-free test is sufficient.
- **Technical Feasibility**: APPROVE ✅
### Round 2 (Completeness / Testability / Clarity / Performance)
- **Completeness**: REQUEST CHANGES — 5 findings, all repeats of Round 1 calibrated-out issues (malformed headers handled by fallback, regex matches documented format, corruption recovery out of scope, count mismatch already specified, subagent failure handling already in prompt). No new actionable issues.
- **Testability**: REQUEST CHANGES — 3 findings, all repeats (batch recomputation mock, subagent dispatch mock, fallback mock). These require mocking kiro-cli internals which is out of scope for ralph_loop.py unit tests. Unit + integration coverage is adequate.
- **Clarity**: REQUEST CHANGES — 5 findings, all rejected (field names are exact, mapping rule placement is logical, dispatch instruction is clear, recomputation timing is explicit, fallback condition is precise).
- **Performance**: APPROVE ✅ — noted O(n²) batch computation and regex re-parsing as optimization opportunities, but correctly assessed they won't cause failures for realistic plan sizes.

**Final status:** Round 1 fixes applied (non-contiguous test, stronger dispatch test, explicit mapping rule). Round 2 reviewers repeated calibrated-out concerns with no new actionable findings. Round 3 used improved structured dispatch queries — quality significantly better: Performance APPROVE, Compatibility reviewer's only finding was factually wrong (test dir exists), Completeness re-raised 1 rejected finding despite explicit list. Testability found 2 valid Nits (verify grep specificity) — fixed. Plan approved.

## Tarefas

### Tarefa 1: PlanFile task parser - extract Task structures with file sets

**Arquivos:**
- Modify: `scripts/lib/plan.py`
- Test: `tests/ralph-loop/test_plan.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_plan.py::test_parse_tasks tests/ralph-loop/test_plan.py::test_parse_tasks_file_sets tests/ralph-loop/test_plan.py::test_parse_tasks_empty_plan -v`

**What to implement:**

Add a `TaskInfo` dataclass (number, name, files set, section_text) and a `parse_tasks()` method to `PlanFile`. The method uses regex to find `^### Task (\d+): (.+)$` headers, then extracts file paths from `^- (?:Create|Modify|Test|Delete): \`path\`` lines within each task section.

**Tests to write** (in `test_plan.py`):
- `test_parse_tasks`: plan with 4 tasks → returns 4 TaskInfo, correct number/name/files
- `test_parse_tasks_file_sets`: tasks sharing `src/shared.py` have overlapping file sets; independent tasks have disjoint sets
- `test_parse_tasks_empty_plan`: plan without task sections → returns `[]`

Test fixtures should use multi-line strings with task headers indented or prefixed to avoid hook false positives.

---

### Tarefa 2: Batch scheduler - group independent tasks

**Arquivos:**
- Create: `scripts/lib/scheduler.py`
- Test: `tests/ralph-loop/test_scheduler.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_scheduler.py -v`

**What to implement:**

Create `scripts/lib/scheduler.py` with:
- `Batch` dataclass: `tasks: list[TaskInfo]`, `parallel: bool`
- `build_batches(tasks, max_parallel=4) -> list[Batch]`: greedy algorithm — pick first remaining task, add all independent tasks (no file overlap) up to max_parallel. Single-task batches are marked `parallel=False`.

**Tests to write** (in `test_scheduler.py`):
- `test_all_independent`: 3 tasks with disjoint files → 1 parallel batch of 3
- `test_all_dependent`: 3 tasks sharing a file → 3 sequential batches of 1
- `test_mixed_deps`: 4 tasks, 2 share a file, 2 independent → independent ones grouped in parallel batch
- `test_max_parallel_cap`: 6 independent tasks with max_parallel=4 → no batch exceeds 4
- `test_empty_tasks`: empty input → `[]`
- `test_single_task`: 1 task → 1 sequential batch

---

### Tarefa 3: Unchecked task filtering - link checklist items to tasks

**Arquivos:**
- Modify: `scripts/lib/plan.py`
- Test: `tests/ralph-loop/test_plan.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks tests/ralph-loop/test_plan.py::test_unchecked_tasks_all_done -v`

**What to implement:**

Add `unchecked_tasks() -> list[TaskInfo]` to `PlanFile`. Strategy: positional mapping — enumerate all checklist items (checked/unchecked/skipped) in order, item at index i corresponds to task i+1. Return tasks whose corresponding checklist item is unchecked.

**Tests to write** (in `test_plan.py`):
- `test_unchecked_tasks`: plan with 3 tasks, first checked → returns tasks 2 and 3
- `test_unchecked_tasks_all_done`: all checked → returns `[]`
- `test_unchecked_tasks_non_contiguous`: plan with 5 tasks, items 1,3,5 checked → returns tasks 2 and 4 only (verifies positional mapping correctness)

**Mapping rule:** enumerate all checklist lines (checked/unchecked/skipped) under `## Checklist` in order. The item at index `i` (0-based) corresponds to task with `number == i+1`. If there are fewer checklist items than tasks, extra tasks are treated as unchecked.

---

### Tarefa 4: Batch-aware prompt generation

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_parallel_prompt_contains_dispatch tests/ralph-loop/test_ralph_loop.py::test_sequential_prompt_no_dispatch -v`

**What to implement:**

Add `build_batch_prompt(batch, plan_path, iteration)` function to `ralph_loop.py`:
- For parallel batches: generate explicit dispatch instructions — list each task with agent_name "executor", mandate use_subagent call, include fallback-to-sequential rule
- For sequential batches: generate single-task implementation instructions (similar to current `build_prompt` but for one specific task)

**Tests to write** (in `test_ralph_loop.py`):
- `test_parallel_prompt_contains_dispatch`: parallel batch prompt contains "executor", "parallel", "use_subagent" or "agent_name", and both task names
- `test_sequential_prompt_no_dispatch`: sequential batch prompt does NOT contain "dispatch"

---

### Tarefa 5: Integrate batch scheduler into ralph_loop.py main loop

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_batch_mode_startup_banner tests/ralph-loop/test_ralph_loop.py::test_dependent_tasks_sequential_banner -v`

**What to implement:**

Modify `ralph_loop.py` main loop:
1. After plan validation, compute batches from `plan.unchecked_tasks()` + `build_batches()`
2. Startup banner shows batch breakdown: `Batch 1: ⚡ parallel [T1, T4]` / `Batch 2: 📝 sequential [T2]`
3. Each iteration processes one batch using `build_batch_prompt()`
4. After each kiro-cli returns, recompute batches from remaining unchecked tasks
5. Keep MAX_ITERATIONS cap and circuit breaker

**Tests to write** (in `test_ralph_loop.py`):
- `test_batch_mode_startup_banner`: plan with 2 independent tasks → stdout contains "batch"
- `test_dependent_tasks_sequential_banner`: plan with 2 tasks sharing a file → stdout contains "sequential"

---

### Tarefa 6: Fallback for plans without structured tasks

**Arquivos:**
- Modify: `scripts/ralph_loop.py`
- Test: `tests/ralph-loop/test_ralph_loop.py`

**Verificação:** `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_fallback_no_task_structure -v`

**What to implement:**

When `plan.unchecked_tasks()` returns empty but `plan.unchecked > 0` (plan has checklist items but no parseable task sections), fall back to the original `build_prompt()` function (item-by-item mode). This ensures backward compatibility.

**Tests to write** (in `test_ralph_loop.py`):
- `test_fallback_no_task_structure`: plan with checklist but no task sections → runs without crash, exits normally

---

### Tarefa 7: Update planning SKILL.md - document batch-aware execution

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**Verificação:** `grep -q 'ralph_loop.py now auto' skills/planning/SKILL.md`

**What to implement:**

Add to Phase 2 Strategy D section:
- Note that ralph_loop.py now auto-analyzes task dependencies
- Agent receives explicit dispatch instructions, no longer needs to judge independence
- Update Strategy Selection table rationale for Strategy D

---

### Tarefa 8: Restructure plan review angles and dispatch template

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**Verificação:** `grep -q 'Goal Alignment' skills/planning/SKILL.md && grep -q 'Verify Correctness' skills/planning/SKILL.md && grep -q 'Dispatch Query Template' skills/planning/SKILL.md`

**What to implement:**

In Phase 1.5 (Plan Review) of `skills/planning/SKILL.md`:

1. **Replace fixed angles.** Change from:
   - Completeness ("Missing steps, unhandled edge cases, gaps")
   - Testability ("Are verify commands adequate?")

   To:
   - **Goal Alignment**: "For each Task, answer: does it contribute to the Goal? Is any task needed for the Goal but missing? Trace execution from Task 1 to final state — does it reach the Goal? Findings must cite specific Task numbers."
   - **Verify Correctness**: "For each checklist verify command: 1) state what it confirms, 2) trace exit code for correct implementation, 3) trace exit code for incorrect implementation. Flag only commands where both traces give same exit code (false positive). Follow the 'Verify Command Review' section in your prompt."

2. **Move Completeness and Testability to the random pool** (replacing them in fixed).

3. **Add Dispatch Query Template** section after Angle Selection:

```markdown
### Dispatch Query Template

Each reviewer query MUST include:

    ## Context
    Goal: [one sentence from plan header]
    Non-Goals: [from plan header]
    Key design decisions that reviewers might mistake for gaps:
    - [decision 1 — what was chosen and what was intentionally excluded]
    - [decision 2]

    ## Your Mission
    This is a PLAN REVIEW (Mode 1 in your prompt).
    [angle-specific mission from the table above]

    ## Read These Files
    Plan: [path]
    Source files referenced in plan: [list — reviewer must read before claiming code behavior]

    ## Anti-patterns (do NOT do these)
    - Do not flag issues outside the stated Goal/Non-Goals
    - Do not suggest alternative approaches that are equally valid
    - Do not flag missing implementation details that an executor agent can infer
    - [plan-specific anti-patterns if any]
```

4. **Add Round 2+ rule** in Orchestration section: "When re-dispatching after fixes, include in each query a 'Rejected Findings' section with one-line summaries of findings rejected in previous rounds and why. Reviewers must not re-raise these."

---

### Tarefa 9: Fix reviewer agentSpawn hook and add executor model to prompt

**Arquivos:**
- Modify: `.kiro/agents/reviewer.json`
- Modify: `agents/reviewer-prompt.md`
- Modify: `scripts/generate_configs.py`

**Verificação:** `jq -r '.hooks.agentSpawn[0].command' .kiro/agents/reviewer.json | grep -q 'Never skip analysis' && grep -q 'Plan Executor Model' agents/reviewer-prompt.md`

**What to implement:**

1. In `.kiro/agents/reviewer.json`, change agentSpawn hook from:
   `"Never rubber-stamp"` → `"Never skip analysis — always read the full plan/diff before giving verdict"`

2. In `agents/reviewer-prompt.md`, add to "Mode 1: Plan Review" section:

```markdown
### Plan Executor Model
Plans are executed by an AI agent with: file read/write, shell execution, code intelligence (LSP),
and web search. The agent can infer implementation details from context — do not flag missing type
annotations, exact function signatures, or step-by-step algorithms unless the approach itself is wrong.
Focus on: is the approach correct? Is the task order right? Are verify commands logically sound?
```

3. Update `scripts/generate_configs.py` to match the new agentSpawn hook text so regeneration doesn't overwrite the fix.

## Checklist

- [x] parse_tasks extrai estrutura de Task corretamente | `python3 -m pytest tests/ralph-loop/test_plan.py::test_parse_tasks -v`
- [x] parse_tasks extrai conjunto de arquivos corretamente | `python3 -m pytest tests/ralph-loop/test_plan.py::test_parse_tasks_file_sets -v`
- [x] parse_tasks com plan vazio retorna lista vazia | `python3 -m pytest tests/ralph-loop/test_plan.py::test_parse_tasks_empty_plan -v`
- [x] build_batches agrupa tarefas totalmente independentes em um grupo | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_all_independent -v`
- [x] build_batches separa tarefas dependentes em grupos isolados | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_all_dependent -v`
- [x] build_batches agrupa misturas de dependencias corretamente | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_mixed_deps -v`
- [x] build_batches respeita max_parallel | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_max_parallel_cap -v`
- [x] build_batches retorna vazio para entrada vazia | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_empty_tasks -v`
- [x] build_batches marca tarefa unica como sequential | `python3 -m pytest tests/ralph-loop/test_scheduler.py::test_single_task -v`
- [x] prompt paralelo contem instrucao de dispatch | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_parallel_prompt_contains_dispatch -v`
- [x] prompt sequencial sem instrucao de dispatch | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_sequential_prompt_no_dispatch -v`
- [x] banner de inicio mostra info do batch | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_batch_mode_startup_banner -v`
- [x] tarefas dependentes marcadas como sequential | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_dependent_tasks_sequential_banner -v`
- [x] unchecked_tasks filtra tarefas concluidas | `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks -v`
- [x] unchecked_tasks com tudo concluido retorna vazio | `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks_all_done -v`
- [x] unchecked_tasks mapeia corretamente check nao contiguo | `python3 -m pytest tests/ralph-loop/test_plan.py::test_unchecked_tasks_non_contiguous -v`
- [x] plan sem estrutura de Task nao quebra | `python3 -m pytest tests/ralph-loop/test_ralph_loop.py::test_fallback_no_task_structure -v`
- [x] documentacao batch-aware atualizada em planning SKILL.md | `grep -q 'ralph_loop.py now auto' skills/planning/SKILL.md`
- [x] angulo do plan review fixo trocado para Goal Alignment + Verify Correctness | `grep -q 'Goal Alignment' skills/planning/SKILL.md && grep -A2 'Goal Alignment' skills/planning/SKILL.md | grep -q 'does it contribute'`
- [x] template de dispatch query adicionado | `grep -q 'Dispatch Query Template' skills/planning/SKILL.md && grep -A3 'Dispatch Query Template' skills/planning/SKILL.md | grep -q 'Non-Goals'`
- [x] regra de Round 2+ rejected findings adicionada | `grep -q 'Rejected Findings' skills/planning/SKILL.md`
- [x] hook agentSpawn do reviewer corrigido | `jq -r '.hooks.agentSpawn[0].command' .kiro/agents/reviewer.json | grep -q 'Never skip analysis'`
- [x] reviewer-prompt recebe executor model | `grep -q 'Plan Executor Model' agents/reviewer-prompt.md`
- [x] generate_configs.py sincroniza alteracao de agentSpawn | `python3 scripts/generate_configs.py && jq -r '.hooks.agentSpawn[0].command' .kiro/agents/reviewer.json | grep -q 'Never skip analysis'`
- [x] todos os testes passam | `python3 -m pytest tests/ralph-loop/ -v`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Descobertas
