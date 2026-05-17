# CN -> PT-BR Translation Final Audit

Branch: `feat/translate-cn-to-ptbr`
Audit date: 2026-03-04 (FEAT-007 closeout)
Audit refresh: 2026-05-17 (post-review v1: cjk-audit.py regex fix + rule D restorations)

## Goal

Translate every Chinese (Mandarin) passage in the repository to Brazilian
Portuguese, except when a passage is a literal pattern that is matched at
runtime (front-matter trigger keywords, regex patterns, test-input strings)
or is verbatim per rule D (fenced code blocks, inline backtick code spans).

## Final state

The repo-wide CJK inventory after FEAT-007 plus the post-review v1 fixes
lists **37 markdown files** that still contain at least one CJK character.
The audit script (`.agents/tasks/task-translate-cn-ptbr/cjk-audit.py`)
splits them into two categories:

- **0 prose-CJK files** outside the documented carve-out group.
- **8 prose-CJK files** in the carve-out group (legitimate per the
  translation contract; see "Carve-out group" below).
- **29 in-fence / inline-code-only CJK files** (legitimate per rule D).

Every doc that contained narrative-prose Chinese has been translated to
PT-BR.

The post-review v1 fix pass restored 6 files that had Chinese shell
comments / bullet content translated *inside* fenced code blocks
(`docs/plans/2026-02-14-framework-v3-deterministic-overhaul.md`,
`docs/plans/2026-02-14-v3-cleanup-and-hardening.md`,
`docs/plans/2026-02-15-subagent-architecture-optimization.md`,
`docs/plans/2026-02-15-workspace-boundary-guard.md`,
`docs/plans/2026-02-18-hook-governance.md`,
`skills/omk-debugging/investigation-template.md`) back to verbatim
Chinese, so the in-fence-only group grew from 25 to 29 files (the four
plan files that previously had only translated comments inside fences
now register CJK again).

## Files translated in this CN -> PT-BR pass

Across FEAT-001 through FEAT-007, the following groups of `.md` files had
their Chinese passages translated to PT-BR:

- `AGENTS.md`, `README.md`, `LICENSE` adjacent docs
- `commands/*.md`
- `.kiro/rules/*.md`
- `templates/agents-sections/*.md`, `templates/agents-types/*.md`
- `skills/omk-*/SKILL.md` and supporting skill markdown
- `knowledge/episodes.md`, `knowledge/rules.md`, `knowledge/INDEX.md`,
  `knowledge/archive/episodes-2026-{02,03}.md`,
  `knowledge/reference/*.md`
- `docs/INDEX.md`, `docs/EXTENSION-GUIDE.md`,
  `docs/designs/2026-02-13-framework-v2-upgrade.md`
- `docs/plans/2026-02-*.md` (60+ files)
- `docs/plans/2026-03-*.md` (autonomous-agent-loop,
  kiro-code-intelligence-integration, ov-auto-sync-recall +
  ov-auto-sync-recall.progress, reasoning-loop-coarse-checklist,
  2026-03-31-evaluator)
- `docs/plans/findings.md`, `docs/plans/progress.md`
- `agents/researcher-prompt.md`, `agents/reviewer-prompt.md`

## Carve-out group (CJK preserved by design)

Eight files retain CJK characters because the CJK is a pattern-matched
literal that the runtime depends on. Translating them would break feature
behavior. Confirmed by reviewing the relevant hooks:

### A. YAML front-matter trigger literals (rule C)

`hooks/feedback/context-enrichment.sh` matches user prompts against the
`description:` and `triggers:` values of skill front-matter. The Chinese
keywords inside these values are runtime regex patterns and must not be
altered:

1. `skills/omk-coding/SKILL.md` (description: trigger keywords like
   `'改代码'`, `'修复'`, `'加个'`, `'改一下'`, `'优化'`)
2. `skills/omk-pdf-gen/SKILL.md` (description: `'生成 PDF'`, `'导出 PDF'`,
   `'做个 PDF'`)
3. `skills/omk-skill-creation/SKILL.md` (description: skill creation
   keyword literals)
4. `skills/omk-stitch/SKILL.md` (triggers: regex literal
   `设计稿|设计.*代码|视觉.*对比`; description: `'做个页面'`, `'用 Stitch 设计'`,
   `'设计系统'`)
5. `skills/omk-youtube/SKILL.md` (description: trigger keywords for the
   YouTube-URL handler)

### B. Test-input literals quoted in plan/test-spec lines (rule D / contract)

These plans document the EXACT user-input strings that hooks must
pattern-match. The Chinese strings are quoted as the literal test inputs
and any change would invalidate the test specification:

6. `docs/plans/2026-02-14-v3-cleanup-and-hardening.md`
   (`"这不是我想要的效果"`, `"换个思路"`, `"今天天气不错"`)
7. `docs/plans/2026-02-18-claude-code-compatibility.md`
   (`"调研一下 X"`, `"你错了，不要用 X"`)

### C. Regex pattern literals quoted in design narrative

8. `docs/plans/2026-02-19-knowledge-auto-evolution.md`
   (the `禁止/必须/never/always` regex tokens that
   `hooks/_lib/distill.sh:53` greps for in episodes)

## In-fence / inline-code-only files (29)

These files have CJK only inside fenced code blocks (` ``` ... ``` `) or
inline backtick code spans (`` `...` ``), which are verbatim per rule D.
No translation is required:

```
.kiro/rules/commands.md
README.md
commands/do.md
docs/designs/2026-02-13-framework-v2-upgrade.md
docs/plans/2026-02-14-framework-v3-deterministic-overhaul.md
docs/plans/2026-02-14-knowledge-base-overhaul.md
docs/plans/2026-02-14-v3-cleanup-and-hardening.md
docs/plans/2026-02-15-command-cleanup.md
docs/plans/2026-02-15-knowledge-integration-test.md
docs/plans/2026-02-15-knowledge-system-v2.md
docs/plans/2026-02-15-ralph-loop-enforcement.md
docs/plans/2026-02-15-reviewing-skill-enhancement.md
docs/plans/2026-02-15-subagent-architecture-optimization.md
docs/plans/2026-02-15-subagent-selective-delegation.md
docs/plans/2026-02-15-tdd-checklist-enforcement.md
docs/plans/2026-02-15-workspace-boundary-guard.md
docs/plans/2026-02-16-instruction-governance.md
docs/plans/2026-02-16-parallel-checklist-execution.md
docs/plans/2026-02-16-ralph-loop-timeout-heartbeat.md
docs/plans/2026-02-16-socratic-thinking-principles.md
docs/plans/2026-02-18-hook-governance.md
docs/plans/2026-02-19-context-optimization.md
docs/plans/2026-02-20-debugging-capability-upgrade.md
docs/plans/2026-02-20-hardening-sprint.md
docs/plans/2026-02-21-fix-parallel-dispatch.md
docs/plans/2026-02-22-cpa-omcc-integration.md
docs/plans/2026-02-23-gtm-omcc-integration.md
docs/plans/2026-02-25-mcp-prompt-commands.md
docs/plans/2026-03-04-openviking-integration.md
skills/omk-debugging/investigation-template.md
```

Note: the four plan files
(`docs/plans/2026-02-14-v3-cleanup-and-hardening.md`,
`docs/plans/2026-02-15-subagent-architecture-optimization.md`,
`docs/plans/2026-02-15-workspace-boundary-guard.md`,
`docs/plans/2026-02-18-hook-governance.md`) plus
`skills/omk-debugging/investigation-template.md` joined this list during
the post-review v1 fix pass: their fenced shell comments / ASCII tree
labels had been translated and were reverted to the original Chinese to
satisfy rule D. They contain no narrative-prose CJK.

## Test-anchored literals confirmation

All 9 test-anchored English literals from the EN -> PT-BR pass still
appear in the repo (count = number of `.md` files containing each):

| Literal | Count |
|---|---|
| `Coding agent` | 4 |
| `GTM` | 9 |
| `Evidence before claims` | 7 |
| `Skill Routing` | 15 |
| `Authority Matrix` | 8 |
| `episodes.md` | 36 |
| `BEGIN OMK PRINCIPLES` | 4 |
| `**Verdict: APPROVE**` | 12 |
| `**Verdict: REQUEST CHANGES**` | 5 |

## Em dashes

No em dashes (`U+2014`) were introduced in any newly-translated prose
line. Pre-existing em dashes that survive in the diff appear only:

- inside backtick code spans (verbatim per rule D), or
- on the matching `-` side of a round-trip diff (translation kept the
  surrounding sentence shape and preserved the original em dash).

## Test counts vs baseline

Baseline counts captured before the CN pass (see
`.agents/tasks/task-translate-cn-ptbr/baseline-*.txt`) match the post-pass
counts exactly:

| Suite | Pass | Fail |
|---|---|---|
| pytest (with documented `--ignore` set) | 60 | 8 |
| `tests/test-agents-template.sh` | 27 | 1 |
| `tests/knowledge/run.sh` | 1 | 2 (3 total scripts) |

The 8 pytest failures, the 1 agents-template failure, and the 2 knowledge
run failures all pre-existed on `main` before the CN translation pass.

## Final commands run for this audit

```bash
find . -name '*.md' -type f \
  -not -path './.git/*' \
  -not -path './.agents/*' \
  -not -path './.pytest_cache/*' \
  -not -path './tests/knowledge/fixtures/*' \
  -exec grep -l -P '[\x{4e00}-\x{9fff}]' {} \; | sort > /tmp/cjk-final.txt
python3 .agents/tasks/task-translate-cn-ptbr/cjk-audit.py > /tmp/cjk-audit-final.txt

python3 -m pytest -q \
  --ignore=tests/test_generate_configs.py \
  --ignore=tests/test_debugging_skill.py \
  --ignore=tests/ralph-loop/test_evaluator.py \
  --ignore=tests/ralph-loop/test_pty_runner.py \
  --ignore=tests/ralph-loop/test_ralph_loop.py
bash tests/test-agents-template.sh
bash tests/knowledge/run.sh
```

## Conclusion

The CN -> PT-BR translation pass is complete. Every Chinese narrative
passage outside the documented carve-out group has been translated to
Brazilian Portuguese while preserving:

- All YAML front-matter (byte-identical for the keys that hooks parse)
- All fenced code blocks (verbatim per rule D)
- All inline backtick code spans (verbatim per rule D)
- All file paths, identifiers, URLs, command flags, and tool names
- All 9 test-anchored English literals
- All baseline test counts

The repository can now be reviewed and merged.
