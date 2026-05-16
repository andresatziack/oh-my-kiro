# Skip List - Files That MUST NOT Be Modified

These files are TEST FIXTURES asserted by `tests/knowledge/l1-*.sh` through
exact substring grep. Editing them (even reformatting whitespace) breaks
tests. They MUST remain byte-for-byte identical across every feature on
`feat/translate-md-ptbr`.

## Hard exclusions (never edit)

- `tests/knowledge/fixtures/episodes-healthy.md`
- `tests/knowledge/fixtures/rules-healthy.md`
- `tests/knowledge/fixtures/rules-corrupted.md`

## Why

The fixture files are grepped for exact substrings such as `JSON = jq`,
`sed.*JSON`, `stat -f`, `Skill 文件不得`, `read/write/shell`, and `testword`
inside `tests/knowledge/l1-rules-injection.sh` and
`tests/knowledge/l1-corruption-recall.sh`. Translating any of these phrases
would silently break the regression suite. The files are documented as
fixtures in `context.json` and in `translation-rules.md` rule 1.

## Scope of the rule

Treat the entire `tests/knowledge/fixtures/` directory as read-only for the
duration of this task. If you discover a `.md` file under that directory
during translation passes, skip it without reading it for translation.
