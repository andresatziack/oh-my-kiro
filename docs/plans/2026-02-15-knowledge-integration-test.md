# Plano de Teste de Integração do Knowledge System

**Objetivo:** Build a 2-layer test suite (hook unit tests + agent integration tests) that validates knowledge system correctness, recall effectiveness, and detects corruption/degradation.
**Arquitetura:** L1 = deterministic shell tests against hooks (context-enrichment, auto-capture, kb-health-report), using fixture data and controlled inputs. L2 = agent integration tests via `kiro-cli chat -a --no-interactive`, checking agent actually uses injected rules and captures corrections. All tests use the existing e2e-v3 lib.sh pattern (pass/fail/json report).
**Tech Stack:** Bash, jq, existing lib.sh test framework, kiro-cli (L2 only)

## Review

### Round 1 (Completeness, Testability, Clarity, YAGNI)
- Completeness: APPROVE — core layers covered, INDEX.md routing is nice-to-have
- Testability: REJECT — 3 checklist verify commands could pass on broken implementations
- Clarity: REJECT — fixture contents undefined, verification methods vague, backup mechanism unspecified
- YAGNI: REJECT — 6 fixtures when 3 suffice, 33 cases with overlap, corruption checks duplicate

**Fixes applied:**
- Consolidated fixtures: 6 → 3 (healthy, corrupted, full). Corrupted fixture covers bloat + wrong sections + contradictions. Full fixture covers capacity + staleness.
- Reduced test cases: removed D7 (orphan rules — structural check not actionable), merged D3/D4 into corruption fixture tests, merged E1 into R1-R3 (already testing per-section injection)
- Added concrete fixture content (exact markdown) so implementer doesn't guess
- Fixed checklist verify commands: #8 checks exit 0 explicitly, #9 uses grep on summary line not tail, #10 checks specific corruption test IDs
- Added backup/restore mechanism to lib.sh spec: `setup_sandbox` copies fixtures to /tmp, overrides KNOWLEDGE_DIR; `teardown_sandbox` removes /tmp dir. Real files never touched.

## Tarefas

### Tarefa 1: Test Infrastructure + Fixtures

**Arquivos:**
- Create: `tests/knowledge/lib.sh` (shared helpers)
- Create: `tests/knowledge/fixtures/rules-healthy.md`
- Create: `tests/knowledge/fixtures/rules-corrupted.md`
- Create: `tests/knowledge/fixtures/episodes-healthy.md`

**lib.sh must provide:**
```bash
# Sandbox: all tests run against /tmp/kb-test-$$/, never real knowledge/
setup_sandbox() {
  SANDBOX="/tmp/kb-test-$$"
  mkdir -p "$SANDBOX"
  cp tests/knowledge/fixtures/*.md "$SANDBOX/"
  # Hooks read from knowledge/ — symlink or override via cd
}
teardown_sandbox() { rm -rf "/tmp/kb-test-$$"; }

# Clear session flags so each test gets fresh injection
clear_session_flags() {
  rm -f /tmp/lessons-injected-*.flag /tmp/agent-correction-*.flag /tmp/kb-changed-*.flag
}
```

Also re-export pass/fail/begin_test/record_result/summary from archive e2e-v3 lib.sh (copy the functions, don't source from archive/).

**Fixture: rules-healthy.md** (4 keyword sections, ~800B):
```markdown
# Agent Rules (Long-term Memory)

## [shell, json, jq, bash]
1. JSON = jq，无条件无例外。禁止 sed/awk/grep 修改 JSON。
2. macOS 用 stat -f，禁止 stat -c（GNU-only）。

## [security, hook, injection]
1. Skill 文件不得包含 HTML 注释（防 prompt injection）。
2. Workspace 边界防护是应用层 hook。

## [workflow, plan, review, verify]
1. 方案 review 必须用真实场景 corner case 检验。
2. Checklist 勾选必须有 verify 命令执行证据。

## [subagent, mcp, delegate]
1. Kiro subagent 只能用 read/write/shell/MCP 四类工具。
2. MCP 补能力已验证可行：ripgrep MCP 在 subagent 中完全可用。
```

**Fixture: rules-corrupted.md** (contradictions + wrong section + bloated >1800B):
```markdown
# Agent Rules (Long-term Memory)

## [shell, json, jq, bash]
1. JSON = jq，无条件无例外。
2. 用 sed 处理 JSON 文件最方便。
3. macOS 用 stat -f。
4. macOS 用 stat -c 获取文件大小。
5. grep -c 无匹配时 exit 1。
6. shell 脚本生成前确认目标平台。
7. 结构化数据用结构化工具。
8. awk 处理 JSON 比 jq 快。

## [security, hook, injection]
1. Skill 文件不得包含 HTML 注释。
2. JSON = jq（这条属于 shell section，放错了）。
3. Workspace 边界防护是应用层 hook。
```
(Pad with additional filler rules to exceed 1800B total)

**Fixture: episodes-healthy.md** (15 entries: 10 active, 3 resolved, 2 promoted, keyword "testword" appears 3x for promotion test):
```markdown
# Episodes (Episodic Memory)

2026-02-01 | active | testword,alpha | 第一次 testword 相关问题
2026-02-02 | active | testword,beta | 第二次 testword 出现
2026-02-03 | active | testword,gamma | 第三次 testword 触发晋升
2026-02-04 | active | docker,deploy | Docker 部署配置问题
2026-02-05 | active | react,frontend | React 组件渲染问题
2026-02-06 | active | python,typing | Python 类型标注遗漏
2026-02-07 | active | golang,goroutine | Goroutine 泄漏排查
2026-02-08 | active | rust,lifetime | Rust 生命周期问题
2026-02-09 | active | nginx,proxy | Nginx 反向代理配置
2026-02-10 | active | redis,cache | Redis 缓存穿透
2026-02-11 | resolved | docker,network | Docker 网络问题已解决
2026-02-12 | resolved | react,state | React 状态管理已解决
2026-02-13 | resolved | python,import | Python 导入问题已解决
2026-02-14 | promoted | oldtool,legacy | 旧工具问题已晋升
2026-02-15 | promoted | oldlib,deprecated | 旧库问题已晋升
```

### Tarefa 2: L1 - Rules Injection Tests (context-enrichment.sh)

**Arquivos:**
- Create: `tests/knowledge/l1-rules-injection.sh`

**Setup per test:** `clear_session_flags`, copy rules-healthy.md to sandbox `knowledge/rules.md`, create empty `knowledge/episodes.md`.

| ID | Scenario | Input JSON | Assert stdout contains | Assert stdout NOT contains |
|----|----------|-----------|----------------------|---------------------------|
| R1 | Exact keyword match (jq) | `{"prompt":"用 jq 处理 JSON"}` | `"JSON = jq"` | `"Skill 文件不得"` (security section) |
| R2 | No keyword → fallback to largest | `{"prompt":"帮我写个函数"}` | `"Rules (general)"` | — |
| R3 | English keyword (security) | `{"prompt":"fix the security hook"}` | `"Skill 文件不得"` | `"JSON = jq"` (shell section) |
| R4 | Empty rules file | `{"prompt":"用 jq"}` + empty rules.md | No crash (exit 0) | `"📚"` (no injection) |
| R5 | Old format fallback (no `## [`) | `{"prompt":"test"}` + rules without section headers | All numbered rules in output | — |
| R6 | Session dedup | Run R1 twice without clearing flag | Second run: empty stdout | `"📚"` |
| R7 | Promoted episodes cleaned | episodes with `| promoted |` lines | `"🧹 Cleaned"` | — |

**Verification method:** `echo '{"prompt":"..."}' | bash hooks/feedback/context-enrichment.sh` from sandbox dir, capture stdout into variable, use `assert_contains` / `assert_not_contains`.

### Tarefa 3: L1 - Auto-capture Tests (auto-capture.sh)

**Arquivos:**
- Create: `tests/knowledge/l1-auto-capture.sh`

**Setup per test:** Copy episodes-healthy.md to sandbox `knowledge/episodes.md`, copy rules-healthy.md to sandbox `knowledge/rules.md`. Auto-capture reads these via relative paths from `$PWD`.

| ID | Scenario | $1 (user msg) | Assert exit code | Assert stdout | Assert file change |
|----|----------|---------------|-----------------|---------------|-------------------|
| C1 | Valid correction | `"别用 sed 处理 YAML，用 yq"` | 0 | `"Auto-captured"` | episodes.md line count +1 |
| C2 | Question filtered | `"为什么这样做？"` | 1 | empty | episodes.md unchanged |
| C3 | No action verb | `"这个结果不太好看"` | 1 | empty | episodes.md unchanged |
| C4 | Duplicate keyword skip | `"别用 docker"` (episodes has docker entry) | 0 | `"Similar episode"` | episodes.md unchanged |
| C5 | Already in rules | `"必须用 jq 处理 JSON"` (rules has jq) | 0 | `"Already in rules"` | episodes.md unchanged |
| C6 | Capacity full (30) | `"换成 pytest"` + 30-entry episodes | 0 | `"at capacity"` | episodes.md unchanged |
| C7 | Garbage — no tech term | `"不对不对"` | 1 | empty | episodes.md unchanged |
| C8 | Promotion hint ≥3x | `"别用 testword"` (episodes has 2 testword entries) | 0 | `"×3"` or `"Similar"` | — |

**Verification method:** `cd $SANDBOX && bash $PROJECT_DIR/hooks/feedback/auto-capture.sh "$MSG"`, check `$?`, stdout, and `wc -l < knowledge/episodes.md`.

### Tarefa 4: L1 - Corruption & Recall Tests

**Arquivos:**
- Create: `tests/knowledge/l1-corruption-recall.sh`

Merged corruption detection + recall effectiveness into one file (both test the same hooks with different fixtures).

**Corruption tests:**

| ID | Scenario | Setup | Assert |
|----|----------|-------|--------|
| D1 | Contradictory rules | rules-corrupted as knowledge/rules.md | `grep -c "jq"` in corrupted file ≥2 (contradiction exists — test validates fixture is testable) |
| D2 | Rules in wrong section | rules-corrupted | `awk` finds "JSON = jq" under `[security]` section |
| D3 | Bloated rules | rules-corrupted (>1800B) | kb-health-report stdout contains `"approaching limit"` |
| D4 | Stale episodes (promote candidate) | episodes-healthy (testword ×3) | kb-health-report stdout contains `"Promote"` |
| D5 | Promoted entries cleaned | episodes with promoted lines | context-enrichment stdout contains `"🧹 Cleaned"`, grep `promoted` returns 0 after |

**Recall tests:**

| ID | Scenario | Input prompt | Assert stdout contains | Assert stdout NOT contains |
|----|----------|-------------|----------------------|---------------------------|
| E1 | Correct section for each keyword | `"jq"` / `"security"` / `"plan review"` / `"subagent"` | Respective section's rule #1 | Other sections' rules |
| E2 | Mixed language | `{"prompt":"fix json parsing bug"}` | `"JSON = jq"` | — |
| E3 | Injection completeness | `{"prompt":"用 jq"}` | Both rule 1 AND rule 2 from shell section | — |
| E4 | No false positive | `{"prompt":"今天天气怎么样"}` | `"Rules (general)"` (fallback) | Should not contain security/subagent specific rules |

### Tarefa 5: L2 - Agent Integration Tests

**Arquivos:**
- Create: `tests/knowledge/l2-agent-integration.sh`

**Setup:** `backup_file knowledge/rules.md && backup_file knowledge/episodes.md` before all tests, `restore_file` after all tests (using lib.sh helpers from e2e-v3).

| ID | Prompt | Timeout | Assert output matches |
|----|--------|---------|----------------------|
| A1 | `"帮我用 sed 修改 package.json 里的版本号"` | 90s | `grep -qiE '(jq\|不.*sed.*json\|禁止.*sed)'` |
| A2 | `"这个项目的安全规则是什么？引用具体文件"` | 60s | `grep -qiE '(security\.md\|rules/\|hooks/)'` |
| A3 | `"你搞错了，macOS 上应该用 stat -f 不是 stat -c"` | 90s | Check episodes.md changed OR stdout contains "Already in rules" |
| A4 | `"这个项目用了什么消息队列？查下项目文件"` | 60s | `grep -qiE '(没有\|未找到\|不确定\|no.*found)'` |
| A5 | `"查下我们之前犯过什么错误"` | 60s | `grep -qiE '(episodes\|教训\|mistakes\|错误记录)'` |

### Tarefa 6: Runner Script

**Arquivos:**
- Create: `tests/knowledge/run.sh`

**Behavior:**
1. Parse args: `--l1-only` (default), `--l2-only`, `--all`
2. L1: Run l1-rules-injection.sh → l1-auto-capture.sh → l1-corruption-recall.sh in sequence
3. L2: Run l2-agent-integration.sh (only with `--l2` or `--all`)
4. Print summary: total pass/fail per script + overall
5. Exit 0 if all pass, exit 1 if any fail

## Checklist

- [x] Test lib exists with sandbox helpers | `test -f tests/knowledge/lib.sh && bash -n tests/knowledge/lib.sh && grep -q 'setup_sandbox' tests/knowledge/lib.sh`
- [x] All 3 fixture files exist and are valid | `test -f tests/knowledge/fixtures/rules-healthy.md && test -f tests/knowledge/fixtures/rules-corrupted.md && test -f tests/knowledge/fixtures/episodes-healthy.md`
- [x] L1 rules injection test has ≥7 cases | `grep -c 'begin_test' tests/knowledge/l1-rules-injection.sh | awk '{exit ($1 >= 7 ? 0 : 1)}'`
- [x] L1 auto-capture test has ≥8 cases | `grep -c 'begin_test' tests/knowledge/l1-auto-capture.sh | awk '{exit ($1 >= 8 ? 0 : 1)}'`
- [x] L1 corruption+recall test has ≥9 cases | `grep -c 'begin_test' tests/knowledge/l1-corruption-recall.sh | awk '{exit ($1 >= 9 ? 0 : 1)}'`
- [x] L2 agent test has ≥5 cases | `grep -c 'begin_test' tests/knowledge/l2-agent-integration.sh | awk '{exit ($1 >= 5 ? 0 : 1)}'`
- [x] Runner exits 0 on L1 pass | `bash tests/knowledge/run.sh --l1-only && echo "RUNNER_OK"  | grep -q "RUNNER_OK"`
- [x] L1 tests all pass | `bash tests/knowledge/run.sh --l1-only 2>&1 | grep -c "✅" | awk '{exit ($1 >= 3 ? 0 : 1)}'`
- [x] Corruption tests detect bad fixtures | `bash tests/knowledge/l1-corruption-recall.sh 2>&1 | grep -c "PASS" | awk '{exit ($1 >= 5 ? 0 : 1)}'`
- [x] No real knowledge files modified | `md5 -q knowledge/rules.md knowledge/episodes.md > /tmp/kb-pre.md5 && bash tests/knowledge/run.sh --l1-only && md5 -q knowledge/rules.md knowledge/episodes.md | diff /tmp/kb-pre.md5 -`
