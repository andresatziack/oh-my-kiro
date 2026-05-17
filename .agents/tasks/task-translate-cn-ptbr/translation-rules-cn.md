# Translation Rules - Chinese -> PT-BR (oh-my-kiro)

These rules are the canonical translator contract for the
`feat/translate-cn-to-ptbr` task. They EXTEND, not replace,
`.agents/tasks/task-translate-md-ptbr/translation-rules.md`. Read that file
first - every rule there still applies.

The rules below clarify how to handle the Chinese (Mandarin) passages that
remained after the EN -> PT-BR pass.

## A. Files that MUST NOT be modified

Same as the previous pass. The 3 fixture files asserted byte-exactly by
`tests/knowledge/l1-*.sh`:

- `tests/knowledge/fixtures/episodes-healthy.md`
- `tests/knowledge/fixtures/rules-healthy.md`
- `tests/knowledge/fixtures/rules-corrupted.md`

These contain Chinese substrings (`Skill 文件不得`, `JSON = jq`,
`用 sed 处理 JSON`, `read/write/shell`, `testword`) asserted by
`l1-rules-injection.sh`, `l1-corruption-recall.sh`, `l1-auto-capture.sh`.
Do not touch any other file under `tests/knowledge/fixtures/` either.

## B. Test-anchored English literals (still apply)

The 9 literals from the previous pass MUST appear unchanged after this pass:

1. `Coding agent` (templates/agents-types/coding.md - test-init-project.sh)
2. `GTM` (templates/agents-types/gtm.md - test-agents-template.sh)
3. `Evidence before claims` (templates/agents-sections/principles.md and AGENTS.md)
4. `Skill Routing` (templates/agents-sections/workflow.md)
5. `Authority Matrix` (templates/agents-sections/authority.md)
6. `episodes.md` (templates/agents-sections/self-learning.md)
7. `BEGIN OMK PRINCIPLES` and the matching END marker, plus the WORKFLOW /
   SELF-LEARNING / AUTHORITY pairs
8. `**Verdict: APPROVE**` (when present in plan/review docs)
9. `**Verdict: REQUEST CHANGES**` (when present in plan/review docs)

Plus `Explore` (workflow.md) and `OMK SECTIONS` (templates/agents-types/coding.md
and gtm.md) - these are also pre-existing English literals to leave alone.

## C. YAML front-matter (still verbatim)

`name`, `description`, `argument-hint`, `disable-model-invocation`, `triggers`,
and any other key already present in front-matter MUST remain byte-identical.

In particular, the value of `description:` is matched at runtime by
`hooks/feedback/context-enrichment.sh` against user prompts. Trigger keywords
inside that value (e.g. `'改代码'`, `'修复'`, `'加个'`, `'改一下'`, `'优化'`,
`'生成 PDF'`, `'导出 PDF'`, `'做个 PDF'`, `'设计稿'`, `'设计.*代码'`,
`'视觉.*对比'`, `'看看这个视频'`, `'帮我看看'`, `'代码写完了'`) are
pattern-matched LITERALS - DO NOT translate them. Keep the whole `description:`
value verbatim.

`triggers:` field (e.g. in `skills/omk-stitch/SKILL.md`) is also a
pattern-matched literal: keep verbatim.

## D. Code, paths, identifiers (still verbatim)

Preserve verbatim:

- Fenced code blocks (` ``` ... ``` `) - including their language tag and any
  Chinese strings inside. The fenced block in `commands/do.md` line 27
  containing `"超时"` is INSIDE a code block - do NOT translate.
- Inline code spans (`` `...` ``).
- URLs and link targets in `[text](url)`.
- File paths (`hooks/feedback/context-enrichment.sh`).
- CLI commands and flags (`git checkout -b`, `--ignore=...`).
- Variable, function, parameter, environment-variable, and config-key names.
- Hook names, skill names, command names, file glob patterns.

## E. Structured data lines (knowledge episodes / rules)

Files like `knowledge/episodes.md`, `knowledge/rules.md`, and
`knowledge/archive/episodes-2026-{02,03}.md` use a pipe-delimited line format:

```
DATE | STATUS | KEYWORDS | SUMMARY
```

For each Chinese-bearing line:

- `DATE` (e.g. `2026-02-13`) - verbatim.
- `STATUS` token (`active`, `resolved`, `promoted`, `pending`) - verbatim
  English literal.
- `KEYWORDS` (comma-separated, often English technical tokens with occasional
  Chinese) - verbatim. Even if a keyword is `调研` or `重构`, keep it - these
  are looked up by the distillation pipeline.
- `SUMMARY` (the only translatable column) - translate Chinese prose to PT-BR.
  Within the summary, keep verbatim:
    - Inline backtick spans
    - Function/file/identifier names
    - Hook names
    - Issue numbers (`#5527`), URLs, paths
    - Tool names (`ralph-loop.sh`, `enforce-ralph-loop.sh`)
    - English technical phrases already in the line
    - Section symbols `①` `②` `③` and emoji
    - Source citations like `来源: kirodotdev/Kiro#5792` -> `Fonte: kirodotdev/Kiro#5792`

The leading `<!-- FORMAT: ... -->` and `<!-- STATUS: ... -->` HTML comments
in `knowledge/episodes.md` describe the schema. Their tokens (`DATE`, `STATUS`,
`KEYWORDS`, `SUMMARY`, `active`, `resolved`, `promoted`) are referenced by the
hook pipeline and the schema documentation - keep these comments unchanged or
only translate the `(Memoria Episodica)` style human-readable parts that were
already translated in the EN pass.

## F. Mixed CN+EN headings

Common pattern in this repo: `## Workflow - 复杂任务先 interview`. Translate
ONLY the Chinese part and keep the English keyword:

- `## Part 0: 调研总结 - 官方最佳实践要点`
  -> `## Part 0: Resumo da pesquisa - principais praticas oficiais`
- `## Identidade` already in PT-BR, keep.
- `## Workflow` (English keyword) - keep.
- `## Skill Routing` (test-anchored English literal) - keep.
- `## Authority Matrix` (test-anchored) - keep.
- `## Roteamento de Skills` already in PT-BR, keep.

## G. Bracketed glosses

Chinese parenthetical glosses after an English term:

- `TDD driven (测试驱动开发)` -> `TDD driven (desenvolvimento orientado a testes)`
- `Fail closed (检测失败时拒绝，不放行)` -> `Fail closed (rejeite quando a deteccao falhar, nao libere)`

The English head term stays in English; only the gloss is translated.

## H. Chinese punctuation

Chinese punctuation should be normalised to ASCII counterparts in the
translated PT-BR text:

- `，` -> `,`
- `。` -> `.`
- `；` -> `;`
- `：` -> `:`
- `？` -> `?`
- `！` -> `!`
- `（` `）` -> `(` `)`
- `「` `」` `“` `”` -> `"`
- `『` `』` `‘` `’` -> `'`
- `、` -> `,`
- `…` -> `...`

Numbered-section markers `①` `②` `③` MAY stay (they are visual cues used
across the corpus and appear in many already-translated lines from the EN
pass). If you choose to convert them, use `(1)` / `(2)` / `(3)` consistently
within the same line.

Do NOT introduce em dashes (`—`). Use `-`, a comma, or rephrase.

## I. Tone

Same as previous pass:

- Use `voce` (informal technical register).
- Professional, concise, technical.
- No em dashes anywhere in translated lines.
- Prefer short sentences. Translate by meaning, not word-for-word.
- Preserve the bullet/heading/table structure of the source line for line.

## J. Files already fully Portuguese

If after CN translation a file no longer contains any CJK, mark it done. The
final-audit grep across the repo (excluding fixtures + .git + .agents) MUST
return an empty list at the end of the task.

## K. Diff hygiene

- Translation commits change ONLY `.md` files.
- Within a `.md` file, only natural-language prose changes. YAML front-matter,
  fenced code blocks, links, paths, inline code, and the test-anchored
  literals must remain identical at the byte level.
- Run `git diff --stat` before each commit and confirm only `.md` files
  appear.
- Run `git grep -n -P '[\x{4e00}-\x{9fff}]' -- '*.md' ':(exclude)tests/knowledge/fixtures/*'`
  after each batch to track progress. The list should shrink monotonically
  toward empty.
