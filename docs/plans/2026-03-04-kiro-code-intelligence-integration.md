# Kiro Code Intelligence Integration

**Objetivo:** Integrate Kiro CLI's code intelligence capabilities (LSP auto-init, codebase overview, pattern_search/rewrite) into OMCC framework rules and skills to maximize agent code analysis quality.
**Não-Objetivos:** Changing hook scripts (hooks are bash, can't call code tool); integrating checkpoint/todos/delegate (not stable or not programmatically accessible); changing generate_configs.py or agent JSON.
**Arquitetura:** Pure documentation changes - update 3 markdown files (1 rule + 1 planning skill + 1 debugging reference) to guide agent behavior toward using code intelligence tools effectively.
**Tech Stack:** Markdown
**Diretório de Trabalho:** `.`

## Review
<!-- Reviewer writes here -->

## Tarefas

### Tarefa 1: Enhance code-analysis.md rule

**Arquivos:**
- Modify: `.kiro/rules/code-analysis.md`

Add 4 new directives:
1. Session cold-start: execute `initialize_workspace` operation when entering a code-heavy project (detected by presence of `.py`, `.ts`, `.rs`, etc.)
2. Explore phase: use `generate_codebase_overview` as first step before diving into specific files
3. Structural code search: use `pattern_search` for finding code patterns (e.g., all error handlers, all API calls) instead of grep
4. Safe code transformation: use `pattern_rewrite` (with dry_run) as sed replacement for structural code changes. Reference `block-sed-json.sh` hook as motivation
5. Document python pattern_search caveat: `def $FUNC($$$):` doesn't work, need `def $FUNC($$$ARGS): $$$BODY`

**Verificação:** `grep -q 'initialize_workspace' .kiro/rules/code-analysis.md && grep -q 'generate_codebase_overview' .kiro/rules/code-analysis.md && grep -q 'pattern_search' .kiro/rules/code-analysis.md && grep -q 'pattern_rewrite' .kiro/rules/code-analysis.md && grep -q 'python' .kiro/rules/code-analysis.md`

### Tarefa 2: Add codebase overview to planning Phase 0

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

In Phase 0 Step 1 ("Form Initial Understanding"), add `generate_codebase_overview` as the recommended first action before reading specific files. One sentence addition, not a restructure.

**Verificação:** `grep -q 'generate_codebase_overview' skills/planning/SKILL.md`

### Tarefa 3: Add pattern_search to debugging reference

**Arquivos:**
- Modify: `skills/debugging/reference.md`

Add a `pattern_search` recipe section after the existing LSP recipes. Show how to use it for bug pattern detection (e.g., find all unchecked error returns, find all subprocess calls without timeout).

**Verificação:** `grep -q 'pattern_search' skills/debugging/reference.md`

## Checklist

- [x] code-analysis.md inclui a instrucao initialize_workspace | `grep -q 'initialize_workspace' .kiro/rules/code-analysis.md`
- [x] code-analysis.md inclui a instrucao generate_codebase_overview | `grep -q 'generate_codebase_overview' .kiro/rules/code-analysis.md`
- [x] code-analysis.md inclui a instrucao pattern_search | `grep -q 'pattern_search' .kiro/rules/code-analysis.md`
- [x] code-analysis.md inclui a instrucao pattern_rewrite | `grep -q 'pattern_rewrite' .kiro/rules/code-analysis.md`
- [x] code-analysis.md documenta cuidados com pattern em python | `grep -q 'python' .kiro/rules/code-analysis.md`
- [x] planning SKILL.md Phase 0 Step 1 inclui codebase overview | `grep -q 'generate_codebase_overview' skills/planning/SKILL.md`
- [x] debugging reference inclui o recipe de pattern_search | `grep -q 'pattern_search' skills/debugging/reference.md`
- [x] todos os arquivos modificados estao com sintaxe correta (sem markdown quebrado) | `for f in .kiro/rules/code-analysis.md skills/planning/SKILL.md skills/debugging/reference.md; do test -f "$f" && grep -qm1 '^# ' "$f" || exit 1; done`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
