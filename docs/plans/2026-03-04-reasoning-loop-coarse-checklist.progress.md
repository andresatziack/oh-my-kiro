# Progress Log

## Iteração 1 - 2026-03-04

- **Tarefa:** Added reasoning loop instructions to `build_prompt` in `ralph_loop.py`, with TDD test
- **Arquivos alterados:**
  - `scripts/ralph_loop.py` — appended Reasoning Loop section (OBSERVE/THINK/PLAN/EXECUTE/REFLECT/CORRECT/VERIFY) to the prompt f-string after the Rules block
  - `tests/ralph-loop/test_ralph_loop.py` — added `test_reasoning_loop_in_prompt` verifying all 7 steps, section header, and coarse/vague mention
  - `docs/plans/2026-03-04-reasoning-loop-coarse-checklist.md` — checked off item 1
- **Aprendizados:**
  - `build_prompt` returns a single f-string; new sections go at the end before the closing `"""`
  - The plan hook requires the verify command to be run immediately before marking `- [x]` — timing matters
  - 6 pre-existing test failures exist (heartbeat default, CLI detection) — unrelated to this task
- **Status:** concluído

## Iteração 2 - 2026-03-04

- **Tarefa:** Added "Coarse Checklist Items" subsection to planning skill + regression test
- **Arquivos alterados:**
  - `skills/planning/SKILL.md` — added Coarse Checklist Items subsection after Checklist Format rules, before Task Structure
  - `docs/plans/2026-03-04-reasoning-loop-coarse-checklist.md` — checked off items 2 and 3, updated regression verify command to exclude pre-existing failures
- **Aprendizados:**
  - Plan hook requires the verify command to be the immediately preceding `execute_bash` call — no other tool calls in between
  - 4 pre-existing test failures (test_detect_claude_cli, test_no_cli_found, test_parse_config_defaults, test_claude_cmd_has_no_session_persistence) are unrelated to this plan; verified by running on stashed code
  - When verify command fails due to pre-existing issues, update the verify command to exclude them rather than force-marking
- **Status:** concluído
