# Upgrade de Capacidade de Debugging - Inteligência Diagnóstica Dirigida por LSP

**Objetivo:** 重写 debugging skill，嵌入 LSP 工具链和诊断证据机制，通过 hook 自动提醒和 rule 强制约束，使 agent 调试从"grep+猜测"升级为"语义分析+证据驱动"。
**Não-Objetivos:** 不新建 subagent；不引入外部工具（只用已有 LSP/code tool）；不改 ralph_loop.py。
**Arquitetura:** 三层保障--Skill 教方法 + Rule 强制工具选择 + Hook 自动提醒。修改 5 个文件，新建 0 个文件。Hook 无法观测 agent 工具调用，因此不做验证闭环；强制力来自 rule 层（agent 内化规则）。
**Tech Stack:** Bash (hooks), Markdown (skill/rules)

## Tarefas

### Tarefa 1: 重写 debugging skill - 嵌入 LSP 工具链

**Arquivos:**
- Modify: `skills/debugging/SKILL.md`
- Modify: `skills/debugging/reference.md`
- Test: `tests/test_debugging_skill.py`

**Step 1: Write failing test**

```python
# tests/test_debugging_skill.py
import pytest
from pathlib import Path

SKILL = Path("skills/debugging/SKILL.md").read_text()
REF = Path("skills/debugging/reference.md").read_text()

class TestDebuggingSkillContent:
    def test_has_tool_decision_matrix(self):
        assert "## Tool Decision Matrix" in SKILL

    def test_has_lsp_tools_in_phase1(self):
        p1_start = SKILL.index("### Phase 1")
        p2_start = SKILL.index("### Phase 2")
        p1 = SKILL[p1_start:p2_start]
        for tool in ["get_diagnostics", "search_symbols", "find_references"]:
            assert tool in p1, f"Phase 1 missing {tool}"

    def test_has_diagnostic_evidence_requirement(self):
        assert "Diagnostic Evidence" in SKILL

    def test_has_pre_post_diagnostics(self):
        assert SKILL.count("get_diagnostics") >= 3

    def test_has_episodes_check(self):
        p1_start = SKILL.index("### Phase 1")
        p2_start = SKILL.index("### Phase 2")
        assert "episodes" in SKILL[p1_start:p2_start].lower()

    def test_has_iron_laws(self):
        s = SKILL.lower()
        assert "goto_definition" in s
        assert "find_references" in s
        assert "get_diagnostics" in s

    def test_preserves_existing_content(self):
        for section in ["Red Flags", "Common Rationalizations", "Quick Reference"]:
            assert section in SKILL, f"Lost existing section: {section}"

    def test_preserves_four_phases(self):
        for phase in ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
            assert phase in SKILL, f"Lost {phase}"

    def test_reference_has_tool_recipes(self):
        for t in ["search_symbols", "goto_definition", "find_references", "get_hover", "get_diagnostics"]:
            assert t in REF, f"Reference missing {t}"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debugging_skill.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Rewrite `skills/debugging/SKILL.md`:
- PRESERVE existing valuable content: Red Flags section, Common Rationalizations table, Quick Reference table, Phase 2-4 detailed steps
- Add Tool Decision Matrix (bug type → tool sequence) — new section before Phase 1
- AUGMENT Phase 1 with LSP tool steps (get_diagnostics → search_symbols → find_references → get_hover → Diagnostic Evidence) — add to existing Phase 1, don't replace
- Add Three Iron Laws (no goto_definition = no modify; no find_references = no refactor; no get_diagnostics = no claim fixed)
- Add episodes.md check as Phase 1 Step 0
- Add pre/post get_diagnostics comparison in Phase 4

Rewrite `skills/debugging/reference.md`:
- Add concrete tool recipes for each LSP tool
- Keep existing multi-component diagnostic patterns

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debugging_skill.py -v`
Expected: PASS

**Step 5: Commit**

### Tarefa 2: 升级 debugging rules - LSP-first 硬规则

**Arquivos:**
- Modify: `.claude/rules/debugging.md`
- Modify: `.kiro/rules/code-analysis.md`
- Test: `tests/test_debugging_rules.py`

**Step 1: Write failing test**

```python
# tests/test_debugging_rules.py
import pytest
from pathlib import Path

class TestDebuggingRules:
    def test_claude_rules_has_lsp(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "get_diagnostics" in r
        assert "goto_definition" in r or "search_symbols" in r

    def test_claude_rules_has_evidence(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "evidence" in r.lower() or "证据" in r

    def test_claude_rules_has_lsp_priority(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "LSP" in r or "lsp" in r

    def test_kiro_code_analysis_covers_debugging(self):
        r = Path(".kiro/rules/code-analysis.md").read_text()
        assert "调试" in r or "debug" in r.lower()
        assert "get_diagnostics" in r
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debugging_rules.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Upgrade `.claude/rules/debugging.md` — add rules 4-7:
4. 调试代码问题必须先用 LSP 工具（get_diagnostics, search_symbols, find_references, goto_definition, get_hover）做语义分析。grep 仅用于注释/字符串/配置。
5. 修 bug 前必须产出诊断证据：用了哪些 LSP 工具、发现了什么、根因判断。无证据不修复。
6. 修复后必须 get_diagnostics 验证，新增 diagnostics 为 0 才算完成。
7. 不熟悉的代码：先 goto_definition 理解实现 → find_references 理解使用 → 再动手改。

Upgrade `.kiro/rules/code-analysis.md` — 新增调试段落，明确 debugging 时 get_diagnostics 为首选工具。

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debugging_rules.py -v`
Expected: PASS

**Step 5: Commit**

### Tarefa 3: Hook 自动触发 - context-enrichment 检测调试场景

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`
- Test: `tests/test_debug_hook_trigger.py`

**Step 1: Write failing test**

```python
# tests/test_debug_hook_trigger.py
import subprocess, json, pytest

HOOK = "hooks/feedback/context-enrichment.sh"

def run_hook(prompt):
    r = subprocess.run(["bash", HOOK], input=json.dumps({"prompt": prompt}),
                       capture_output=True, text=True, timeout=10)
    return r.stdout

class TestDebugHookTrigger:
    def test_chinese_error(self):
        assert "🐛" in run_hook("测试报错了，帮我看看")

    def test_english_error(self):
        assert "🐛" in run_hook("tests are failing, looks like something broke")

    def test_bug_keyword(self):
        assert "🐛" in run_hook("这个 bug 怎么修")

    def test_traceback(self):
        assert "🐛" in run_hook("got a traceback in the logs")

    def test_broken_keyword(self):
        assert "🐛" in run_hook("build is broken after the last commit")

    def test_bug_english(self):
        assert "🐛" in run_hook("there's a bug in the parser")

    def test_no_false_positive_chinese(self):
        out = run_hook("帮我写个新功能")
        assert "🐛" not in out

    def test_no_false_positive_error_handling(self):
        out = run_hook("add error handling to the parser")
        assert "🐛" not in out

    def test_no_false_positive_debug_logging(self):
        out = run_hook("add debug logging to the service")
        assert "🐛" not in out
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debug_hook_trigger.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
在 context-enrichment.sh 的 Research reminder 之后添加：
```bash
# Debugging skill reminder + flag
if echo "$USER_MSG" | grep -qE '(报错|bug|调试|修复.*错误|测试失败|不工作了)'; then
  echo "🐛 Debug detected → read skills/debugging/SKILL.md. Use LSP tools (get_diagnostics, search_symbols, find_references) BEFORE attempting fixes."
elif echo "$USER_MSG" | grep -qiE '(\btest.*(fail|brok)|traceback|exception.*thrown|crash|not working|fix.*bug|\bis broken\b|\bbug\b)'; then
  echo "🐛 Debug detected → read skills/debugging/SKILL.md. Use LSP tools (get_diagnostics, search_symbols, find_references) BEFORE attempting fixes."
fi
```

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debug_hook_trigger.py -v`
Expected: PASS

**Step 5: Commit**


## Checklist

- [x] debugging skill 包含 Tool Decision Matrix | `grep -q 'Tool Decision Matrix' skills/debugging/SKILL.md`
- [x] debugging skill Phase 1 引用 LSP 工具 | `python3 -c "t=open('skills/debugging/SKILL.md').read(); p1=t[t.index('### Phase 1'):t.index('### Phase 2')]; assert all(x in p1 for x in ['get_diagnostics','search_symbols','find_references'])"`
- [x] debugging skill 要求诊断证据 | `grep -q 'Diagnostic Evidence' skills/debugging/SKILL.md`
- [x] debugging skill 包含三铁律 | `grep -q 'goto_definition' skills/debugging/SKILL.md && grep -q 'find_references' skills/debugging/SKILL.md`
- [x] reference.md 包含工具 recipes | `python3 -c "t=open('skills/debugging/reference.md').read(); assert all(x in t for x in ['search_symbols','goto_definition','find_references','get_hover','get_diagnostics'])"`
- [x] debugging rules 包含 LSP 要求 | `grep -q 'get_diagnostics' .claude/rules/debugging.md && grep -qE '(LSP|lsp)' .claude/rules/debugging.md`
- [x] kiro code-analysis 覆盖调试场景 | `grep -qE '(调试|debug)' .kiro/rules/code-analysis.md && grep -q 'get_diagnostics' .kiro/rules/code-analysis.md`
- [x] context-enrichment 检测中文调试 | `echo '{"prompt":"测试报错了"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] context-enrichment 检测英文调试 | `echo '{"prompt":"tests are failing"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] context-enrichment 不误触发 | `! echo '{"prompt":"帮我写个新功能"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] 全部测试通过 | `python3 -m pytest tests/test_debugging_skill.py tests/test_debugging_rules.py tests/test_debug_hook_trigger.py -v`

## Review

### Round 1 (4 reviewers)

- **Goal Alignment:** REQUEST CHANGES — Task 4 只提供软警告，不是硬拦截，与目标"强制诊断证据机制"和"验证闭环"不符。建议：要么升级为硬拦截，要么调整目标措辞。Task 1-3 与目标对齐良好，执行顺序无依赖问题，non-goals 均被尊重。
- **Verify Correctness:** REQUEST CHANGES — 3 个问题：(1) Checklist "不误触发"项用 `grep -qv '🐛'`，多行输出时永远 pass（false positive），应改为 `! grep -q '🐛'`；(2) Checklist "stop hook 检查 LSP 使用"引用 `tests/verify_debug_stop_hook.sh` 但该文件不存在且不在 plan 文件列表中；(3) verify-completion.sh 有 early exit 路径（stop_hook_active=true 或有 unchecked items），Task 4 的 debug 验证代码可能永远不执行。
- **Completeness:** REQUEST CHANGES — 3 个问题：(1) 现有 SKILL.md 200+ 行丰富内容（Red Flags、Common Rationalizations、Quick Reference 等），测试只检查关键词存在，rewrite 可能丢失有价值内容；(2) "investigate" 同时出现在 research 和 debug 检测 grep 中，会双重触发；(3) 4 个测试文件未纳入 CI 配置。
- **Technical Feasibility:** REQUEST CHANGES — 2 个 blocker：(1) verify-log 没有写入端——没有任何组件记录 LSP 工具使用到 verify-log，Task 4 的检查永远告警（架构级缺陷）；(2) grep 'error'/'fail' 误触发率极高（"error handling"、"fail-safe" 等正常讨论都会触发）。另外 flag 文件基于 workspace hash 而非 session，多次调试覆盖问题。

### Round 2 fixes applied

| Issue | Fix |
|-------|-----|
| Task 4 verify-log 无写入端（架构不可行） | 删除 Task 4。Goal 从"验证闭环"降级为"hook 自动提醒 + rule 强制约束"。Hook 无法观测 agent 工具调用，强制力来自 rule 层 |
| grep 'error'/'fail' 误触发 | 收紧英文模式为 `test.*(fail\|brok)\|traceback\|exception.*thrown\|crash\|not working\|fix.*bug\|is broken\|\\bbug\\b`，排除 "error handling"/"debug logging" 等正常讨论 |
| `grep -qv` false positive | 改为 `! grep -q` |
| `tests/verify_debug_stop_hook.sh` 不存在 | 删除该 checklist 项（Task 4 已删除） |
| SKILL.md rewrite 可能丢失内容 | 添加 PRESERVE 指令 + 内容保留测试（Red Flags, Common Rationalizations, Quick Reference, 4 Phases） |
| "investigate" 与 research 检测重叠 | 收紧英文模式已排除 investigate |
| flag 文件无用（Task 4 已删除） | 删除 flag 文件写入 |

### Round 2 re-review (2 reviewers)

- **Fixes verification:** APPROVE — all 7 fixes correctly address Round 1 issues. No new problems introduced.
- **Technical Feasibility (grep patterns):** REQUEST CHANGES — `broke` doesn't match `broken`, `bug` removed from English pattern. **Fixed:** `broke` → `brok` (matches broke/broken), added `\bis broken\b` and `\bbug\b`. Trade-off accepted: `getting an error` still missed but adding `error` would reintroduce false positives.

**Final verdict: APPROVE (Round 2 pattern fix applied, all angles satisfied)**

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Descobertas

