# Translation Rules - EN -> PT-BR (oh-my-kiro)

These rules are the canonical translator contract for the `feat/translate-md-ptbr`
task. Every later feature on this branch MUST follow them. They exist to keep
test-anchored literals, runtime-matched front-matter, and machine-consumed
artifacts intact while turning explanatory English prose into Brazilian
Portuguese.

## 1. Files that MUST NOT be modified

The following files are test fixtures asserted by `tests/knowledge/l1-*.sh`
through exact substring grep. Any edit will break tests. They are also listed
in `skip-list.md`:

- `tests/knowledge/fixtures/episodes-healthy.md`
- `tests/knowledge/fixtures/rules-healthy.md`
- `tests/knowledge/fixtures/rules-corrupted.md`

Do not touch any other file under `tests/knowledge/fixtures/` either.

## 2. Test-anchored English literals

The bash test harness greps for exact English phrases inside specific
templates. These literals MUST appear unchanged after translation:

- `templates/agents-sections/principles.md` - must contain `Evidence before claims`.
- `templates/agents-sections/workflow.md` - must contain `Explore` and `Skill Routing`.
- `templates/agents-sections/self-learning.md` - must contain `episodes.md`.
- `templates/agents-sections/authority.md` - must contain `Authority Matrix`.
- `templates/agents-types/coding.md` - must contain `Coding agent` and `OMK SECTIONS`.
- `templates/agents-types/gtm.md` - must contain `GTM`.

HTML region markers in `templates/agents-sections/*.md` are also test-anchored
and must remain byte-for-byte:

- `<!-- BEGIN OMK PRINCIPLES -->` / `<!-- END OMK PRINCIPLES -->`
- `<!-- BEGIN OMK WORKFLOW -->` / `<!-- END OMK WORKFLOW -->`
- `<!-- BEGIN OMK SELF-LEARNING -->` / `<!-- END OMK SELF-LEARNING -->`
- `<!-- BEGIN OMK AUTHORITY -->` / `<!-- END OMK AUTHORITY -->`
- Any other `<!-- BEGIN OMK ... -->` / `<!-- END OMK ... -->` pair.

## 3. YAML front-matter

YAML front-matter blocks at the top of skill / command / agent / template
files MUST be preserved byte-for-byte. In particular:

- Keys: `name`, `description`, `argument-hint`, `disable-model-invocation`,
  and any other key already present.
- The value of `description:` is matched at runtime by
  `hooks/feedback/context-enrichment.sh` against user prompts. Trigger
  keywords inside that value (e.g. `write code`, `implement`, `fix this`)
  are pattern-matched literals. To stay safe, keep the entire `description:`
  value verbatim - do not translate it.
- Indentation, quoting style, and trailing whitespace inside the front-matter
  must not change.

## 4. Code, paths, identifiers

Preserve verbatim:

- Fenced code blocks (` ``` ... ``` `) - including their language tag.
- Inline code spans (`` `...` ``).
- URLs and link targets in `[text](url)`.
- File paths (e.g. `hooks/feedback/context-enrichment.sh`).
- CLI commands and flags (`git checkout -b`, `--ignore=...`).
- Variable, function, parameter, environment-variable, and config-key names.

## 5. Technical acronyms (kept in English)

`API`, `SDK`, `CLI`, `IAM`, `VPC`, `DNS`, `HTTP`, `HTTPS`, `JSON`, `YAML`,
`TOML`, `LSP`, `MCP`, `AST`, `TDD`, `SOLID`, `GAN`, `URL`, `URI`, `TTL`,
`CRUD`, `REPL`, `DSL`, `RPC`, `gRPC`, `SLA`, `SLO`, `KPI`, `OS`, `ID`, `UUID`,
`PR`, `MR`.

## 6. Tool / product / framework names (kept in English)

`AWS`, `Kiro`, `MCP`, `CDK`, `CloudFormation`, `Terraform`, `Docker`,
`GitHub`, `Git`, `GraphQL`, `OpenViking`, `Ralph Loop`, `Claude`,
`Anthropic`, `Python`, `Bash`, `Node.js`, `npm`, `pip`, `pytest`, `jq`,
`sed`, `grep`, `Markdown`, `YAML`, `JSON`.

## 7. Consecrated technical terms (kept in English)

These verbs and nouns stay in English even inside Portuguese sentences:
`deploy`, `commit`, `push`, `pull request`, `endpoint`, `payload`, `token`,
`middleware`, `runtime`, `framework`, `pipeline`, `webhook`, `hook`, `gate`,
`build`, `lint`, `test`, `plan`, `review`, `scratchpad`, `worktree`,
`submodule`, `branch`, `merge`, `rebase`, `override`, `rollout`, `rollback`,
`feature flag`, `log`, `flag`.

## 8. What to translate

- Explanatory prose (paragraphs of narrative English).
- Headings (translate the natural-language part, keep technical terms per
  rules 5 to 7 - e.g. `## Skill Routing` stays, `## Why this matters`
  becomes `## Por que isso importa`).
- List bullets and numbered list items written in English prose.
- Table cells written as natural language.
- Image alt text, blockquote prose, captions.

## 9. Style and tone

- Use the second person singular `você` (informal technical register).
- Professional, concise, technical tone - matches the original in voice.
- Do NOT use em dashes (`—`). Use a regular hyphen `-`, a comma, or rephrase
  the sentence.
- Prefer short sentences. Translate by meaning, not word-for-word, when the
  literal translation would be awkward.
- Keep sentence-level punctuation (`.`, `;`, `:`, `?`, `!`) one-to-one with
  the source where possible.

## 10. Files already in Portuguese or Chinese

- If a file is ALREADY entirely in Brazilian Portuguese, SKIP it unchanged
  and record the skip in the feature's `findings`.
- If a file is ENTIRELY in Chinese (no English prose to translate), SKIP
  it unchanged and record the skip. Do NOT translate Chinese to Portuguese.
- For mixed Chinese + English files (very common in this repo, including
  `AGENTS.md` and most files under `docs/plans/`), translate ONLY the
  English passages. Leave Chinese passages exactly as they are.

## 11. Diff hygiene

- Translation commits must change ONLY `.md` files.
- Within a `.md` file, only natural-language prose should change. YAML
  front-matter, code blocks, links, paths, and test-anchored phrases must
  remain identical at the byte level.
- Run `git diff --stat` before each commit and confirm only `.md` files
  appear and only prose lines are touched.
