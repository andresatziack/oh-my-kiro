# Enforcement de Checklist TDD - Qualidade do Plan + Integridade da Execução

**Objetivo:** 通过代码化机制杜绝 plan checklist 虚假勾选、覆盖率不足、agent 能力降级三大问题，实现端到端的测试驱动质量保障。
**Arquitetura:** 四层防护：(1) Plan 写入时 Static Rubric 检查结构完整性；(2) Reviewer prompt 增强强制覆盖率审查；(3) 执行阶段 hook 拦截无证据勾选；(4) Stop hook 重跑所有 verify 命令做最终确认。核心设计：每个 checklist 项必须包含可执行 verify 命令，勾选前必须有该命令的成功执行记录。
**Tech Stack:** Shell (bash), jq, Markdown

## Key Decisions

1. **Verify 命令格式**：`- [ ] 描述 | \`verify command\``，用 ` | \` ` 分隔描述和命令，机器可解析，人可读。不用 HTML comment（rules.md 禁止 skill 文件含 HTML comment，保持一致）
2. **执行记录机制**：bash PostToolUse hook 将每条命令的 hash + exit code + timestamp 写入 `/tmp/verify-log-<workspace-hash>.jsonl`。勾选时 PreToolUse hook 检查该 log 中是否有对应 verify 命令的成功记录（exit 0，10 分钟内）
3. **Plan 结构检查用 PreToolUse hook**：写入 `docs/plans/*.md` 时检查结构（有 Task、有 Verify、有 Checklist），不通过则 exit 2 硬拦截
4. **Reviewer 增强用 prompt 约束**：在 reviewer-prompt.md 中加入 checklist 覆盖率检查要求 + 对抗性测试场景补充要求
5. **Stop hook 增强**：verify-completion.sh 不只数勾，还提取所有 verify 命令重新执行，任何失败 = 未完成
6. **不做 Red-Green 强制**：调研后发现本项目是 shell hook 框架（非应用代码），大部分 verify 是 grep/jq 断言而非 unit test，强制 Red-Green 会增加大量复杂度但收益有限。保留 planning skill 中的 TDD 建议，但不用 hook 强制
7. **不做测试文件锁定**：同理，本项目没有传统意义的 test 文件，verify 命令嵌在 plan 中
8. **~~30 分钟窗口~~ → 10 分钟窗口**：reviewer 指出 30 分钟太长允许过期结果，改为 10 分钟
9. **Log 原子写入**：用 `>>` append 写入（POSIX 保证 ≤PIPE_BUF 的 write 是原子的，单行 JSON ≪ 4096 字节），不需要 flock
10. **Workspace hash 保持 8 字符**：这是 session 级临时文件，不是持久存储。同一台机器同时跑两个不同项目的概率极低，且即使碰撞也只是多了无关记录不影响正确性（查询时按 cmd_hash 精确匹配）
11. **不做命令规范化**：verify 命令是从 plan 文件中精确提取的，写入 log 时也是精确记录。同一个 verify 命令在 plan 中只有一种写法，不存在 `echo "test"` vs `echo 'test'` 的问题
12. **Log 自动清理**：verify-completion stop hook 执行完后清理当前 workspace 的 log 文件
13. **verify-completion 中 verify 命令加 timeout**：防止无限循环，每个命令 30 秒超时

## Tarefas

### Tarefa 1: 创建 verify 执行记录器 - post-bash-verify-log.sh

**Arquivos:**
- Modify: `hooks/feedback/post-write.sh`（在现有 post-write 中增加 bash 执行记录逻辑，但实际需要的是 PostToolUse[execute_bash]，需要新文件）
- Create: `hooks/feedback/post-bash.sh`

PostToolUse[execute_bash] hook，每次 bash 命令执行后记录：
```jsonl
{"cmd_hash":"<sha1 of command>","cmd":"<command>","exit_code":0,"ts":1739612345}
```

写入 `/tmp/verify-log-<workspace-hash>.jsonl`。

逻辑：
```bash
#!/bin/bash
source "$(dirname "$0")/../_lib/common.sh"
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)
case "$TOOL_NAME" in
  execute_bash|Bash) ;;
  *) exit 0 ;;
esac

CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
EXIT_CODE=$(echo "$INPUT" | jq -r '.tool_output.exit_code // .tool_output.exitCode // "0"' 2>/dev/null)
[ -z "$CMD" ] && exit 0

WS_HASH=$(pwd | shasum 2>/dev/null | cut -c1-8 || echo "default")
LOG_FILE="/tmp/verify-log-${WS_HASH}.jsonl"
CMD_HASH=$(echo "$CMD" | shasum 2>/dev/null | cut -c1-40 || echo "unknown")
TS=$(date +%s)

echo "{\"cmd_hash\":\"$CMD_HASH\",\"cmd\":$(echo "$CMD" | jq -Rs .),\"exit_code\":$EXIT_CODE,\"ts\":$TS}" >> "$LOG_FILE"
exit 0
```

**Verificação:** `echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"},"tool_output":{"exit_code":"0"}}' | bash hooks/feedback/post-bash.sh && tail -1 /tmp/verify-log-*.jsonl | jq .cmd_hash` 输出非空 hash

### Tarefa 2: 创建 checklist 勾选拦截 hook - gate-checklist-check.sh

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh`（在现有 pre-write 中增加 checklist 勾选检查逻辑）

在 pre-write.sh 的 gate_check 函数之后、scan_content 之前，增加 checklist 勾选拦截：

检测条件：写入目标是 `docs/plans/*.md`，且 `new_str` / `content` 中包含 `- [x]`

拦截逻辑：
1. 从写入内容中提取所有 `- [x] ... | \`command\`` 的 verify 命令
2. 对每个 verify 命令，计算 cmd_hash，在 verify-log 中查找 30 分钟内 exit_code=0 的记录
3. 任何一个 verify 命令没有成功记录 → exit 2 硬拦截，提示 "Run the verify command first"
4. 如果 `- [x]` 行没有 verify 命令（无 ` | \` ` 分隔符）→ exit 2 硬拦截，提示 "Checklist item missing verify command"

```bash
# Phase 1.5: Checklist check-off gate
gate_checklist() {
  case "$FILE" in
    docs/plans/*.md) ;;
    *) return 0 ;;
  esac

  # Detect check-off: content contains "- [x]"
  echo "$CONTENT" | grep -q '\- \[x\]' || return 0

  WS_HASH=$(pwd | shasum 2>/dev/null | cut -c1-8 || echo "default")
  LOG_FILE="/tmp/verify-log-${WS_HASH}.jsonl"
  NOW=$(date +%s)
  WINDOW=600  # 10 minutes

  # Extract all checked items from the write content
  echo "$CONTENT" | grep '\- \[x\]' | while IFS= read -r line; do
    # Extract verify command after " | `"
    VERIFY_CMD=$(echo "$line" | sed -n 's/.*| `\(.*\)`$/\1/p')

    if [ -z "$VERIFY_CMD" ]; then
      hook_block "🚫 BLOCKED: Checklist item checked without verify command.
Item: $line
Required format: - [ ] description | \`verify command\`
Every checklist item must have an executable verify command."
    fi

    # Check verify log for recent successful execution
    CMD_HASH=$(echo "$VERIFY_CMD" | shasum 2>/dev/null | cut -c1-40)
    if [ ! -f "$LOG_FILE" ]; then
      hook_block "🚫 BLOCKED: No verify execution log found. Run the verify command first.
Item: $line
Command: $VERIFY_CMD"
    fi

    RECENT=$(jq -r --arg h "$CMD_HASH" --argjson now "$NOW" --argjson w "$WINDOW" \
      'select(.cmd_hash == $h and .exit_code == 0 and ($now - .ts) < $w)' \
      "$LOG_FILE" 2>/dev/null | head -1)

    if [ -z "$RECENT" ]; then
      hook_block "🚫 BLOCKED: Verify command not recently executed (or failed).
Item: $line
Command: $VERIFY_CMD
Run the command and confirm it passes before checking off."
    fi
  done
}
```

**Verificação:** 
- 测试 A：写入含 `- [x]` 但无 verify 命令的 plan → exit 2
- 测试 B：写入含 `- [x] ... | \`echo test\`` 但未执行过 → exit 2
- 测试 C：先执行 `echo test`（写入 log），再写入含对应 `- [x]` → exit 0 放行

### Tarefa 3: Plan 结构 Static Rubric 检查

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh`

在 gate_checklist 之前增加 plan 结构检查（仅对 `docs/plans/*.md` 的 create 操作）：

检查项：
1. 必须有 `## Tasks` section
2. 必须有 `## Checklist` section
3. 必须有至少一个 `### Task` 
4. 每个 `### Task` 必须有 `**Verify:**` 行
5. `## Checklist` 中每个 `- [ ]` 必须包含 ` | \`command\`` 格式的 verify 命令
6. Checklist 项数 ≥ Task 数（每个 task 至少一个验证项）

```bash
gate_plan_structure() {
  case "$FILE" in
    docs/plans/*.md) ;;
    *) return 0 ;;
  esac
  # Only check on create (full content available)
  [ "$COMMAND" = "create" ] || [ "$TOOL_NAME" = "Write" ] || return 0

  # Check required sections
  echo "$CONTENT" | grep -q '^## Tasks' || \
    hook_block "🚫 BLOCKED: Plan missing ## Tasks section."
  echo "$CONTENT" | grep -q '^## Checklist' || \
    hook_block "🚫 BLOCKED: Plan missing ## Checklist section."
  echo "$CONTENT" | grep -q '^## Review' || \
    hook_block "🚫 BLOCKED: Plan missing ## Review section."

  # Check tasks have verify
  TASK_COUNT=$(echo "$CONTENT" | grep -c '^### Task' || true)
  [ "${TASK_COUNT:-0}" -eq 0 ] && \
    hook_block "🚫 BLOCKED: Plan has no ### Task sections."

  VERIFY_COUNT=$(echo "$CONTENT" | grep -c '^\*\*Verify:\*\*' || true)
  [ "${VERIFY_COUNT:-0}" -lt "${TASK_COUNT}" ] && \
    hook_block "🚫 BLOCKED: Not all Tasks have **Verify:** lines. Tasks=$TASK_COUNT, Verify=$VERIFY_COUNT"

  # Check checklist items have verify commands
  CHECKLIST_TOTAL=$(echo "$CONTENT" | sed -n '/^## Checklist/,/^## /p' | grep -c '^\- \[ \]' || true)
  [ "${CHECKLIST_TOTAL:-0}" -eq 0 ] && \
    hook_block "🚫 BLOCKED: ## Checklist section has no items."

  CHECKLIST_WITH_VERIFY=$(echo "$CONTENT" | sed -n '/^## Checklist/,/^## /p' | grep '^\- \[ \]' | grep -c '| `' || true)
  [ "${CHECKLIST_WITH_VERIFY}" -lt "${CHECKLIST_TOTAL}" ] && \
    hook_block "🚫 BLOCKED: $((CHECKLIST_TOTAL - CHECKLIST_WITH_VERIFY))/$CHECKLIST_TOTAL checklist items missing verify command.
Required format: - [ ] description | \`verify command\`"

  # Minimum coverage: checklist items >= task count
  [ "${CHECKLIST_TOTAL}" -lt "${TASK_COUNT}" ] && \
    hook_block "🚫 BLOCKED: Checklist items ($CHECKLIST_TOTAL) < Task count ($TASK_COUNT). Need at least 1 verify per task."
}
```

**Verificação:** 
- 测试 A：写入缺少 `## Checklist` 的 plan → exit 2
- 测试 B：写入 checklist 项无 verify 命令的 plan → exit 2
- 测试 C：写入完整结构的 plan → exit 0

### Tarefa 4: 增强 verify-completion Stop hook

**Arquivos:**
- Modify: `hooks/feedback/verify-completion.sh`

在现有 checklist 计数之后，增加 verify 命令重跑逻辑：

```bash
# Re-run all verify commands from checked items
if [ -n "$ACTIVE_PLAN" ] && [ -f "$ACTIVE_PLAN" ]; then
  FAILED=0
  TOTAL=0
  sed -n '/^## Checklist/,/^## /p' "$ACTIVE_PLAN" | grep '^\- \[x\]' | while IFS= read -r line; do
    VERIFY_CMD=$(echo "$line" | sed -n 's/.*| `\(.*\)`$/\1/p')
    [ -z "$VERIFY_CMD" ] && continue
    TOTAL=$((TOTAL + 1))
    if ! timeout 30 bash -c "$VERIFY_CMD" > /dev/null 2>&1; then
      FAILED=$((FAILED + 1))
      echo "❌ VERIFY FAILED: $VERIFY_CMD"
      echo "   Item: $line"
    fi
  done
  [ "$FAILED" -gt 0 ] && echo "🚫 $FAILED/$TOTAL verify commands failed. Work is NOT complete."

  # Cleanup verify log
  WS_HASH=$(pwd | shasum 2>/dev/null | cut -c1-8 || echo "default")
  [ -f "/tmp/verify-log-${WS_HASH}.jsonl" ] && : > "/tmp/verify-log-${WS_HASH}.jsonl"
fi
```

**Verificação:** 构造一个含 `- [x] test | \`exit 1\`` 的 plan，stop hook 应报告 verify failed

### Tarefa 5: 增强 Reviewer prompt - 覆盖率 + 对抗性测试

**Arquivos:**
- Modify: `agents/reviewer-prompt.md`
- Modify: `skills/reviewing/SKILL.md`

在 reviewer-prompt.md 的 Plan Review mode 中增加：

```markdown
## Checklist Coverage Review (mandatory for plan review)
After reviewing the plan's logic, you MUST also:
1. Check every `### Task` has a `**Verify:**` line with an executable command (not "手动测试")
2. Check `## Checklist` items all have `| \`verify command\`` format
3. For each Task, verify the checklist covers:
   - At least 1 happy path verification
   - At least 1 edge case or error scenario
   - Integration with existing functionality (if applicable)
4. Propose at least 2 test scenarios the plan author missed per Task
5. If any of the above is missing → automatic REQUEST CHANGES

Output these findings in a dedicated "### Checklist Coverage" subsection of your review.
```

**Verificação:** `grep -c 'Checklist Coverage' agents/reviewer-prompt.md` ≥ 1

### Tarefa 6: 挂载新 hook 到 agent 配置

**Arquivos:**
- Modify: `.kiro/agents/default.json`
- Modify: `.kiro/agents/reviewer.json`
- Modify: `.kiro/agents/researcher.json`
- Modify: `scripts/generate-platform-configs.sh`

为所有 agent 添加 PostToolUse[execute_bash] → post-bash.sh。
pre-write.sh 已挂载，无需额外配置（新逻辑在现有 hook 内）。

**Verificação:** `jq '.hooks.postToolUse[] | select(.command | contains("post-bash"))' .kiro/agents/default.json` 输出非空

### Tarefa 7: 更新 planning skill - 新 checklist 格式

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

更新 plan 模板中的 Checklist 格式要求：

```markdown
## Checklist Format (enforced by hook)

Every checklist item MUST include an executable verify command:
```
- [ ] description | `verify command`
```

Examples:
- [ ] hook 语法正确 | `bash -n hooks/security/my-hook.sh`
- [ ] config 包含新 hook | `jq '.hooks.preToolUse[] | select(.command | contains("my-hook"))' .kiro/agents/default.json | grep -q my-hook`
- [ ] 测试 A: 外部路径被拦截 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"/tmp/evil.txt"}}' | bash hooks/security/my-hook.sh 2>&1; test $? -eq 2`

Rules:
- Verify command must be executable (no "手动测试", no "目视检查")
- Verify command must return exit 0 on success
- Each Task must have at least 1 checklist item
- Cover: happy path + edge case + integration (where applicable)
```

**Verificação:** `grep -c 'verify command' skills/planning/SKILL.md` ≥ 3

### Tarefa 8: 记录到 knowledge

**Arquivos:**
- Modify: `knowledge/episodes.md`
- Modify: `knowledge/rules.md`

episodes.md 追加本次实现记录。
rules.md 的 workflow section 追加：checklist 勾选必须有 verify 命令执行证据，hook 强制。

**Verificação:** `grep -c 'verify' knowledge/episodes.md` ≥ 1

## Review

### Checklist Coverage ✅
- All 8 Tasks have **Verificação:** lines with executable commands
- ## Checklist section exists with 12 concrete `- [ ]` items
- All checklist items follow `| \`command\`` format
- Coverage: 12 checklist items ≥ 8 tasks (minimum requirement met)

### Strengths
- **Comprehensive 4-layer defense**: Static structure check → reviewer enforcement → execution gate → stop-time verification
- **Machine-parseable format**: `| \`command\`` separator enables reliable extraction
- **Tamper-proof execution log**: SHA1 hashes + timestamps prevent gaming
- **Fail-fast approach**: PreToolUse hooks block invalid operations immediately
- **Integration with existing hooks**: Builds on pre-write.sh and verify-completion.sh

### Critical Issues
1. **Race condition in verify log**: Multiple agents could write to same `/tmp/verify-log-*.jsonl` simultaneously, corrupting JSON lines. Need file locking or atomic writes.

2. **Workspace hash collision**: `pwd | shasum | cut -c1-8` could collide across different projects. Use full path + inode for uniqueness.

3. **Command normalization missing**: `echo "test"` vs `echo 'test'` vs `echo test` have different hashes but same intent. Need command canonicalization.

### Warnings
1. **30-minute window too long**: Allows stale verify results. Consider 5-10 minutes max.

2. **No verify command validation**: Malicious commands like `rm -rf /` could be embedded. Need command sanitization.

3. **Log file cleanup missing**: `/tmp/verify-log-*.jsonl` will accumulate indefinitely. Need rotation/cleanup.

4. **Error handling gaps**: What if `jq` fails, `shasum` unavailable, or `/tmp` readonly? Need fallback strategies.

### Missing Edge Cases & Test Scenarios

**Task 1 (post-bash.sh) - Missing scenarios:**
- Concurrent execution: Two agents running same command simultaneously
- Malformed JSON input: Invalid tool_output structure
- System limits: `/tmp` full or readonly filesystem
- Command with special chars: Pipes, redirects, quotes in command string

**Task 2 (checklist gate) - Missing scenarios:**
- Partial matches: `- [x]` in code blocks or comments (false positives)
- Time zone changes: Verify executed before daylight saving time shift
- Log corruption: Truncated or invalid JSON lines in verify log
- Hash collisions: Different commands producing same SHA1 (extremely rare but possible)

**Task 3 (plan structure) - Missing scenarios:**
- Nested sections: `### Task` inside code blocks
- Unicode content: Non-ASCII characters in task descriptions
- Large files: Plans exceeding shell variable limits
- Malformed markdown: Missing newlines, broken section headers

**Task 4 (verify-completion) - Missing scenarios:**
- Infinite loops: Verify commands that never terminate
- Environment changes: Commands that depend on specific PATH/env vars
- Resource exhaustion: Verify commands consuming excessive CPU/memory
- Network dependencies: Commands requiring internet access

**Task 5 (reviewer prompt) - Missing scenarios:**
- Reviewer bypass: Agent ignoring prompt instructions
- Ambiguous requirements: What constitutes "sufficient" coverage?
- Reviewer disagreement: Multiple reviewers with conflicting opinions
- Prompt injection: Malicious content in plan affecting reviewer behavior

**Task 6 (agent config) - Missing scenarios:**
- Config validation: Invalid JSON after modification
- Hook ordering: post-bash.sh conflicts with other PostToolUse hooks
- Agent inheritance: Subagents not inheriting hook configuration
- Platform differences: Windows vs Unix path handling

**Task 7 (planning skill) - Missing scenarios:**
- Template conflicts: Existing plans using old format
- Skill versioning: Multiple planning skill versions in use
- User confusion: Developers not understanding new format requirements
- Migration path: Converting existing plans to new format

**Task 8 (knowledge update) - Missing scenarios:**
- Knowledge conflicts: New rules contradicting existing ones
- Search indexing: Updated content not reflected in searches
- Version control: Knowledge changes not properly tracked
- Access control: Who can modify knowledge files?

### Suggestions
1. **Add command whitelist**: Only allow safe verify commands (grep, jq, test, etc.)
2. **Implement log rotation**: Clean up verify logs older than 24 hours
3. **Add verification metrics**: Track verify success rates, common failures
4. **Create debug mode**: Verbose logging for troubleshooting hook issues
5. **Add plan migration tool**: Convert existing plans to new format

### Verdict: REQUEST CHANGES

**Blocking issues requiring fixes:**
1. Fix race condition in verify log writing (file locking)
2. Improve workspace hash uniqueness (full path + inode)
3. Add command normalization for consistent hashing
4. Implement verify log cleanup mechanism
5. Add error handling for missing dependencies (jq, shasum)

**Recommended before implementation:**
- Add command sanitization/whitelist
- Reduce verify window to 10 minutes
- Add comprehensive error handling
- Create test suite for all edge cases identified above

### Round 2 Review

**Fixes Applied ✅:**
- ✅ Verify window reduced from 30 min to 10 min (Decision 8)
- ✅ Log cleanup added to verify-completion stop hook (Decision 12)
- ✅ Timeout 30s added to verify command re-execution (Decision 13)
- ✅ Race condition addressed: POSIX `>>` append ≤PIPE_BUF is atomic (Decision 9)
- ✅ Workspace hash collision: explained as non-issue for session-level temp files (Decision 10)
- ✅ Command normalization: explained as non-issue since verify commands are extracted from plan verbatim (Decision 11)

**Remaining Concerns:**
- jq/shasum dependency not explicitly checked — acceptable since both are already used throughout the framework and verified at setup
- No command whitelist — acceptable for v1, verify commands are written by the agent itself (not user input), and the plan is reviewed before execution

**Verdict: APPROVE**

The Round 1 blocking issues have been adequately addressed through design decisions with clear rationale. The 10-minute window, timeout protection, and log cleanup resolve the practical concerns. The remaining items are acceptable risks for a v1 implementation.

## Checklist
- [x] post-bash.sh 存在且记录 bash 执行到 jsonl | `test -f hooks/feedback/post-bash.sh && bash -n hooks/feedback/post-bash.sh`
- [x] post-bash.sh 正确记录命令 hash 和 exit code | `echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"},"tool_output":{"exit_code":"0"}}' | bash hooks/feedback/post-bash.sh && tail -1 /tmp/verify-log-*.jsonl | jq -e '.cmd_hash'`
- [x] pre-write.sh 拦截无 verify 命令的 checklist 勾选 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] done"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] pre-write.sh 拦截无执行记录的 checklist 勾选 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] done | \`echo never_ran_this_xyz\`"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] pre-write.sh 放行有执行记录的 checklist 勾选 | `echo test_verify_pass | shasum | cut -c1-40 | xargs -I{} sh -c 'echo "{\"cmd_hash\":\"{}\",\"cmd\":\"test_verify_pass\",\"exit_code\":0,\"ts\":$(date +%s)}" >> /tmp/verify-log-*.jsonl' && echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] pass | \`test_verify_pass\`"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 0`
- [x] plan 结构检查：缺少 ## Checklist 被拦截 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] plan 结构检查：checklist 项无 verify 被拦截 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n## Checklist\n- [ ] item without verify\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] plan 结构检查：完整 plan 放行 | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n## Checklist\n- [ ] item | \`echo ok\`\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 0`
- [x] verify-completion stop hook 重跑 verify 命令 | `grep -q 'VERIFY FAILED\|verify commands' hooks/feedback/verify-completion.sh`
- [x] reviewer prompt 包含 Checklist Coverage 要求 | `grep -c 'Checklist Coverage' agents/reviewer-prompt.md`
- [x] default.json 包含 post-bash hook | `jq -e '.hooks.postToolUse[] | select(.command | contains("post-bash"))' .kiro/agents/default.json`
- [x] planning skill 包含新 checklist 格式说明 | `grep -c 'verify command' skills/planning/SKILL.md`
- [x] knowledge 已记录 | `grep -c 'tdd-checklist' knowledge/episodes.md`
