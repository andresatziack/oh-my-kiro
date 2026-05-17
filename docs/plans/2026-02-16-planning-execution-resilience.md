# Aprimoramento de Resiliência na Execução do Planning

**Objetivo:** Enhance the planning skill with 5 mechanisms from planning-with-files and industry best practices to prevent drift, error loops, and context loss during execution.
**Não-Objetivos:** Not replacing the existing plan structure; not introducing multi-file systems (task_plan/findings/progress); not adding external script dependencies.
**Arquitetura:** Add 3 new sections to the Phase 1 plan template (Non-Goals, Errors, Findings), and add 3 execution disciplines to Phase 2 (Read Before Decide, 3-Strike Error Protocol, Session Resume + Periodic Re-orientation). All changes in a single file: `skills/planning/SKILL.md`.
**Tech Stack:** Markdown

## Review

**Round 1:** Completeness REQUEST CHANGES (error log growth, session boundary), Testability REQUEST CHANGES (grep too shallow, phase check weak), Clarity APPROVE, Compatibility APPROVE. → Fixed: added error log cap, replaced grep with sed location-aware checks.

**Round 2:** Completeness APPROVE, Testability REQUEST CHANGES (phase count check, Non-Goals position), Technical Feasibility APPROVE, Performance APPROVE. → Fixed: exact count validation, precise pattern matching.

**Final status:** All issues addressed. Plan ready for user confirmation.

## Tarefas

### Tarefa 1: Enhance Plan Header Template (Phase 1)

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**What to change in Phase 1 → Plan Header:**

Add `**Non-Goals:**` field after Goal line. This explicitly declares what's out of scope, preventing implicit scope expansion (inspired by GSCP-15's ScopeLock concept).

Current:
```markdown
**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
```

New:
```markdown
**Goal:** [One sentence]
**Non-Goals:** [What this plan explicitly does NOT do]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
```

### Tarefa 2: Add Errors Section to Plan Template (Phase 1)

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**What to add after the Task Structure (TDD) section, before Phase 1.5:**

A new subsection documenting that every plan must include an `## Errors` section:

```markdown
### Errors Section (required)

Every plan must have an `## Errors` section at the bottom. During execution, log every error encountered:

\`\`\`markdown
## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
\`\`\`

Rules:
- Log immediately when error occurs, don't wait
- Include which Task triggered the error
- Track attempt number — if same error appears at attempt 3, trigger 3-Strike Protocol (see Phase 2)
- This section is append-only during execution — never delete entries
- Cap: keep most recent 20 entries; if exceeded, summarize older entries into a single "Earlier errors: N resolved" row
```

### Tarefa 3: Add Findings Section to Plan Template (Phase 1)

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**What to add after the Errors Section:**

```markdown
### Findings Section (optional)

Plans may include a `## Findings` section for persisting research discoveries made during execution:

\`\`\`markdown
## Findings

- [discovery with context]
\`\`\`

Rules:
- Append-only — never rewrite, only add new entries
- Use when execution-phase research reveals something relevant to later tasks
- Not required for simple plans where no research happens during execution
```

### Tarefa 4: Add Execution Disciplines to Phase 2

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**What to add at the beginning of Phase 2, before the strategy selection table:**

```markdown
### Execution Disciplines

These rules apply regardless of which execution strategy is chosen.

#### Session Resume Protocol

When starting or resuming execution (including new sessions):
1. Read the plan's Goal + Architecture + Non-Goals
2. Run `git diff --stat` to see what's already changed
3. Check checklist: which items are `[x]` done, which `[ ]` remain
4. Write a one-line status summary to the plan's `## Findings` section

This ensures the agent has full context before making any changes.

#### Read Before Decide

Before any of these actions, re-read the plan's **Goal** and **Non-Goals**:
- Changing implementation approach mid-task
- Deciding to skip or reorder a task
- Encountering a blocker and choosing a workaround
- Adding scope not in the original plan

This pushes the original intent back into the attention window, preventing drift after many tool calls.

#### Periodic Re-orientation

Every 3 completed tasks, re-read the plan's **Goal** paragraph. No writing needed — purely attention refresh. This counters gradual context decay in long execution sessions.

#### 3-Strike Error Protocol

When an error occurs during execution:

**Strike 1 — Diagnose & Fix:** Read error carefully, identify root cause, apply targeted fix. Log to `## Errors`.

**Strike 2 — Alternative Approach:** Same error? Try a fundamentally different method. Different tool, different algorithm, different angle. Log to `## Errors`.

**Strike 3 — Broader Rethink:** Question assumptions. Search for solutions. Consider whether the plan itself needs revision. Log to `## Errors`.

**After 3 strikes:** Stop and escalate to user. Explain what was tried, share the specific errors, ask for guidance. Do NOT attempt a 4th time with the same approach.

Rules:
- `next_action != failed_action` — never repeat the exact same failing approach
- Each strike must be logged in the plan's `## Errors` table with attempt number
- Strike count is per-error-type, not global (different errors get their own 3 strikes)
```

## Checklist

- [x] Non-Goals na area do Plan Header | `sed -n '/^### Plan Header/,/^###[^#]/p' skills/planning/SKILL.md | grep -q '\*\*Non-Goals:\*\*'`
- [x] Errors Section dentro da area Phase 1 | `sed -n '/^## Phase 1: Writing/,/^## Phase 1.5/p' skills/planning/SKILL.md | grep -q 'Errors Section'`
- [x] Findings Section dentro da area Phase 1 | `sed -n '/^## Phase 1: Writing/,/^## Phase 1.5/p' skills/planning/SKILL.md | grep -q 'Findings Section'`
- [x] Execution Disciplines dentro da area Phase 2 | `sed -n '/^## Phase 2/,/^## Phase 3/p' skills/planning/SKILL.md | grep -q 'Execution Disciplines'`
- [x] Session Resume Protocol existe | `sed -n '/^## Phase 2/,/^## Phase 3/p' skills/planning/SKILL.md | grep -q 'Session Resume Protocol'`
- [x] Read Before Decide existe | `sed -n '/^## Phase 2/,/^## Phase 3/p' skills/planning/SKILL.md | grep -q 'Read Before Decide'`
- [x] Periodic Re-orientation existe | `sed -n '/^## Phase 2/,/^## Phase 3/p' skills/planning/SKILL.md | grep -q 'Periodic Re-orientation'`
- [x] 3-Strike Error Protocol existe | `sed -n '/^## Phase 2/,/^## Phase 3/p' skills/planning/SKILL.md | grep -q '3-Strike Error Protocol'`
- [x] os 5 titulos de Phase originais permanecem completos | `test "$(grep -c '## Phase\|## Overview\|## When to Stop' skills/planning/SKILL.md)" -ge 7`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Descobertas

