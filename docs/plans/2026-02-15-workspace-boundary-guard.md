# Guarda de Fronteira do Workspace

**Objetivo:** 阻止 agent 写入 workspace 以外的文件，防止破坏系统文件。
**Arquitetura:** 新建 `hooks/security/block-outside-workspace.sh`，同时挂到 `fs_write` 和 `execute_bash` 两个 matcher。fs_write 用 realpath 精确检查目标路径；bash 用正则检测明显的外部写入模式。所有 agent（default/reviewer/researcher）+ Claude Code 配置统一挂载。
**Tech Stack:** Shell (bash), jq

## Key Decisions

1. **方案 B**：fs_write 路径检查 + bash 外部写入模式检测，workspace 内不限制
2. **硬拦截**（exit 2），不是警告
3. **所有 agent** 统一挂载（default + reviewer + researcher）
4. **Workspace = git root**，fallback 到 `$PWD`；检测失败则 block 所有写入（fail-closed）
5. **单文件实现**：一个 hook 脚本处理两种 tool_name（fs_write 和 execute_bash），通过 tool_name 分支
6. **Hook 顺序**：block-outside-workspace 在 pre-write.sh 之前（先安全检查，再 workflow gate）
7. **不做的事**：symlink 攻击、race condition、unicode 攻击、process substitution — 这些是 OS 级沙箱的职责，应用层 hook 做不到也不该做。我们的目标是拦截 agent 的 **正常误操作**，不是防御恶意 prompt injection 的高级攻击

## Tarefas

### Tarefa 1: 创建 block-outside-workspace.sh

**Arquivos:**
- Create: `hooks/security/block-outside-workspace.sh`

脚本逻辑：

```bash
#!/bin/bash
# block-outside-workspace.sh — PreToolUse[fs_write + execute_bash]
# Blocks file writes outside the workspace boundary.
source "$(dirname "$0")/../_lib/common.sh"

INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // ""' 2>/dev/null)

# Determine workspace root (fail-closed: if detection fails, block all writes)
WORKSPACE=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
if [ -z "$WORKSPACE" ] || [ "$WORKSPACE" = "/" ]; then
  hook_block "🚫 BLOCKED: Cannot determine workspace root. Refusing all writes for safety."
fi

case "$TOOL_NAME" in
  fs_write|Write|Edit)
    FILE=$(echo "$INPUT" | jq -r '.tool_input.file_path // .tool_input.path // ""' 2>/dev/null)
    [ -z "$FILE" ] && exit 0

    # Expand ~ and $HOME
    FILE=$(echo "$FILE" | sed "s|^~|$HOME|; s|\\\$HOME|$HOME|g")

    # Resolve to absolute path (handle both existing and new files)
    if [ -e "$FILE" ]; then
      RESOLVED=$(realpath "$FILE" 2>/dev/null || echo "$FILE")
    elif [ -e "$(dirname "$FILE")" ]; then
      RESOLVED="$(realpath "$(dirname "$FILE")" 2>/dev/null)/$(basename "$FILE")"
    else
      # Parent doesn't exist — resolve relative to PWD, collapse ../
      case "$FILE" in
        /*) RESOLVED="$FILE" ;;
        *)  RESOLVED="$(pwd)/$FILE" ;;
      esac
      # Collapse ../ sequences using Python (available on macOS)
      RESOLVED=$(python3 -c "import os; print(os.path.normpath('$RESOLVED'))" 2>/dev/null || echo "$RESOLVED")
    fi

    case "$RESOLVED" in
      "$WORKSPACE"/*|"$WORKSPACE") exit 0 ;;
    esac

    hook_block "🚫 BLOCKED: Write outside workspace.
Target: $FILE → $RESOLVED
Workspace: $WORKSPACE
Agent may only write files inside the workspace."
    ;;

  execute_bash|Bash)
    CMD=$(echo "$INPUT" | jq -r '.tool_input.command // ""' 2>/dev/null)
    [ -z "$CMD" ] && exit 0

    # Patterns that indicate writing outside workspace
    # Covers: redirect (> >>), tee, cp, mv, install, ln, tar -C
    OUTSIDE_WRITE_PATTERNS=(
      '>+\s*/etc/'
      '>+\s*/usr/'
      '>+\s*/var/'
      '>+\s*/tmp/'
      '>+\s*/opt/'
      '>+\s*~/\.'
      '>+\s*~/'
      '>+\s*\$HOME/'
      'tee\s+(-a\s+)?(/etc/|/usr/|/var/|~/|~/.|\$HOME/)'
      '\b(cp|mv|install)\b.*\s+(/etc/|/usr/|/var/|~/|~/.|\$HOME/)'
      '\bln\b.*\s+(/etc/|/usr/|/var/|~/|~/.|\$HOME/)'
      '\btar\b.*-C\s*(/etc/|/usr/|/var/|~/|\$HOME/)'
    )

    for pattern in "${OUTSIDE_WRITE_PATTERNS[@]}"; do
      if echo "$CMD" | grep -qiE "$pattern"; then
        hook_block "🚫 BLOCKED: Bash command writes outside workspace.
Command: $CMD
Matched: $pattern
Workspace: $WORKSPACE
Use paths inside the workspace instead."
      fi
    done
    ;;
esac

exit 0
```

**Verificação:** `bash -n hooks/security/block-outside-workspace.sh` 无语法错误；`ls -la hooks/security/block-outside-workspace.sh` 确认可执行

### Tarefa 2: 更新所有 Kiro agent JSON - 挂载新 hook

**Arquivos:**
- Modify: `.kiro/agents/default.json`
- Modify: `.kiro/agents/reviewer.json`
- Modify: `.kiro/agents/researcher.json`

每个 agent 的 `preToolUse` 数组中添加两条：
```json
{"matcher": "fs_write", "command": "hooks/security/block-outside-workspace.sh"},
{"matcher": "execute_bash", "command": "hooks/security/block-outside-workspace.sh"}
```

default.json 已有 `fs_write` matcher（pre-write.sh），新 hook 加在它之前（先安全检查，再 workflow gate）。
reviewer/researcher 之前没有 fs_write matcher，直接新增。

**Verificação:** `jq '.hooks.preToolUse[] | select(.command | contains("block-outside-workspace"))' .kiro/agents/{default,reviewer,researcher}.json | jq -s 'length'` = 6（每个 agent 2 条 × 3 个 agent）

### Tarefa 3: 更新 Claude Code 配置 - generate-platform-configs.sh

**Arquivos:**
- Modify: `scripts/generate-platform-configs.sh`

在 `.claude/settings.json` 生成部分：
- `PreToolUse` Bash matcher 的 hooks 数组中添加 `block-outside-workspace.sh`
- `PreToolUse` 新增 `Write|Edit` matcher 的 hooks 中添加 `block-outside-workspace.sh`（在 pre-write.sh 之前）

在 reviewer/researcher agent 生成部分：
- `preToolUse` 数组中添加 fs_write + execute_bash 两条 block-outside-workspace 配置

**Verificação:** `bash scripts/generate-platform-configs.sh && grep -c 'block-outside-workspace' .claude/settings.json .kiro/agents/*.json` - .claude/settings.json ≥ 2，每个 agent json ≥ 2

### Tarefa 4: 手动测试 hook

**测试 A: fs_write 拦截外部路径**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"/tmp/evil.txt","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**测试 B: fs_write 放行 workspace 内路径**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"hooks/test.txt","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 0, 无输出
```

**测试 C: bash 拦截外部写入**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello > ~/.zshrc"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**测试 D: bash 放行正常命令**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 0, 无输出
```

**测试 E: fs_write 拦截路径穿越**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"../../../etc/passwd","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**测试 F: bash 拦截 append 重定向**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo data >> ~/evil.txt"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**测试 G: bash 拦截 tar -C 外部路径**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"tar -xf archive.tar -C /usr/local/"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Verificação:** 4 个测试全部通过

### Tarefa 5: 记录到 knowledge

**Arquivos:**
- Modify: `knowledge/episodes.md`
- Modify: `knowledge/rules.md`

episodes.md 追加本次实现记录。
rules.md 如有相关 rule 则更新，否则新增 workspace boundary rule。

**Verificação:** `grep -c 'workspace' knowledge/episodes.md` ≥ 1

## Review

**Category: Critical**

### Strengths
- Clear security objective with hard blocking (exit 2) approach
- Comprehensive coverage: both fs_write path checking and bash pattern detection
- Single hook script handling multiple tool types reduces maintenance overhead
- Proper workspace detection with git root fallback to PWD
- Concrete test cases covering both positive and negative scenarios
- Complete checklist with verifiable acceptance criteria ✅

### Weaknesses
- **Path resolution logic is fragile**: The realpath approach for new files may fail if parent directories don't exist, potentially allowing bypasses
- **Regex patterns are incomplete**: Missing dangerous patterns like `echo "data" >> /etc/hosts`, `cat > /usr/local/bin/script`, or indirect writes via variables
- **No symlink attack protection**: Malicious symlinks could bypass workspace boundaries
- **Case sensitivity gaps**: Patterns don't account for case variations in commands (TEE, Tee, etc.)
- **Shell injection vulnerability**: Using `echo "$CMD" | grep -qE` without proper escaping could be exploited

### Missing Critical Elements
- **Relative path traversal protection**: `../../../etc/passwd` patterns not handled
- **Environment variable expansion**: `$HOME`, `${PWD}/../..` could bypass detection
- **Indirect file operations**: `find . -name "*.txt" -exec cp {} /tmp/ \;` not covered
- **Archive operations**: `tar -xf archive.tar -C /usr/local/` bypasses detection
- **Process substitution**: `>(cat > /etc/file)` syntax not detected
- **Error handling**: No validation that workspace detection succeeded
- **Logging**: No audit trail of blocked attempts for security monitoring

### High-Risk Edge Cases
1. **Workspace detection failure**: If both `git rev-parse` and `$PWD` fail, script continues with empty workspace
2. **Race conditions**: File creation between path resolution and actual write
3. **Mount point confusion**: Different filesystems could confuse path resolution
4. **Unicode/encoding attacks**: Non-ASCII paths might bypass string matching
5. **Command chaining**: `cd /tmp && echo data > file` bypasses workspace check

### Missing Implementation Details
- No integration with existing `pre-write.sh` workflow - potential conflicts
- Hook ordering not specified (should block-outside-workspace run before or after pre-write.sh?)
- No consideration of performance impact on large workspaces
- Missing rollback plan if hook causes false positives

### Verdict: REQUEST CHANGES

**Required fixes before approval:**
1. Add comprehensive path traversal protection (`../`, `./../../`, etc.)
2. Expand regex patterns to cover indirect writes, archives, and process substitution
3. Add proper symlink resolution and validation
4. Implement robust error handling for workspace detection failures
5. Add case-insensitive pattern matching
6. Specify hook execution order relative to existing hooks
7. Add security logging for blocked attempts

**Recommended additions:**
- Whitelist mechanism for legitimate external writes (e.g., `/tmp/kiro-*`)
- Performance optimization for large directory trees
- Integration tests with actual agent execution

### Round 2 Review

**Category: Critical**

#### Fixes Applied ✅
- **Path traversal**: Python3 normpath properly collapses `../` sequences
- **Fail-closed**: Empty workspace detection now blocks all writes
- **Append redirect**: `>+` regex covers both `>` and `>>` patterns
- **tar -C**: Added to bash pattern detection
- **Case insensitive**: `grep -qiE` flag applied
- **Hook ordering**: Explicitly before pre-write.sh
- **New tests**: E, F, G cover path traversal, append, tar scenarios

#### Remaining Issues ⚠️
- **Regex escaping**: `echo "$CMD" | grep -qiE "$pattern"` still vulnerable to shell injection if CMD contains regex metacharacters
- **Variable expansion**: `$HOME` expansion in bash commands not detected (e.g., `echo data > $HOME/.evil`)
- **Command chaining**: `cd /tmp && echo data > file` bypasses workspace check

#### Assessment
The core security gaps from Round 1 are adequately addressed. The path normalization using Python3 is robust, fail-closed behavior prevents bypasses during workspace detection failures, and pattern coverage is significantly improved.

The remaining issues are edge cases that would require sophisticated prompt injection to exploit. For the stated goal of preventing "agent 正常误操作" rather than defending against malicious attacks, this implementation provides sufficient protection.

#### Verdict: **APPROVE**

The plan now meets security requirements for preventing accidental agent writes outside workspace boundaries. The documented scope limitations (Decision 7) appropriately exclude OS-level attack vectors that belong in system sandboxing rather than application hooks.

## Checklist
- [x] `hooks/security/block-outside-workspace.sh` 存在且可执行
- [x] hook 语法正确（`bash -n` 通过）
- [x] workspace 检测失败时 fail-closed（block 所有写入）
- [x] default.json preToolUse 包含 block-outside-workspace（fs_write + execute_bash 两条）
- [x] reviewer.json preToolUse 包含 block-outside-workspace（fs_write + execute_bash 两条）
- [x] researcher.json preToolUse 包含 block-outside-workspace（fs_write + execute_bash 两条）
- [x] generate-platform-configs.sh 包含 block-outside-workspace 配置
- [x] `.claude/settings.json` 生成后包含 block-outside-workspace
- [x] 测试 A: fs_write 外部路径被拦截（exit 2）
- [x] 测试 B: fs_write workspace 内路径放行（exit 0）
- [x] 测试 C: bash 外部写入被拦截（exit 2）
- [x] 测试 D: bash 正常命令放行（exit 0）
- [x] 测试 E: fs_write 路径穿越被拦截（exit 2）
- [x] 测试 F: bash append 重定向被拦截（exit 2）
- [x] 测试 G: bash tar -C 外部路径被拦截（exit 2）
- [x] knowledge 已记录
