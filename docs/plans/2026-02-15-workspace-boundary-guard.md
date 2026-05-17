# Guarda de Fronteira do Workspace

**Objetivo:** Bloquear gravacoes do agent fora do workspace, prevenindo dano a arquivos do sistema.
**Arquitetura:** Criar `hooks/security/block-outside-workspace.sh`, registrado nos matchers `fs_write` e `execute_bash`. fs_write usa realpath para checar o caminho alvo com precisao; bash usa regex para detectar padroes obvios de escrita externa. Todos os agents (default/reviewer/researcher) e a configuracao do Claude Code recebem o hook.
**Tech Stack:** Shell (bash), jq

## Key Decisions

1. **Estrategia B**: validacao de path em fs_write + deteccao de padroes de escrita externa em bash; sem restricao dentro do workspace
2. **Bloqueio forte** (exit 2), nao warning
3. **Todos os agents** recebem o hook (default + reviewer + researcher)
4. **Workspace = git root**, com fallback para `$PWD`; se a deteccao falhar, bloqueia toda escrita (fail-closed)
5. **Implementacao em arquivo unico**: um script que trata os dois tool_name (fs_write e execute_bash) com branch por tool_name
6. **Ordem do hook**: block-outside-workspace antes de pre-write.sh (primeiro a checagem de seguranca, depois o workflow gate)
7. **Fora de escopo**: ataque com symlink, race condition, ataque com unicode, process substitution - sao responsabilidade do sandbox a nivel de SO; um hook de aplicacao nao consegue tratar e nao deve. O objetivo aqui e interceptar **erros operacionais comuns do agent**, nao atacante sofisticado via prompt injection

## Tarefas

### Tarefa 1: criar block-outside-workspace.sh

**Arquivos:**
- Create: `hooks/security/block-outside-workspace.sh`

Logica do script:

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

**Verificação:** `bash -n hooks/security/block-outside-workspace.sh` sem erro de sintaxe; `ls -la hooks/security/block-outside-workspace.sh` confirma que e executavel

### Tarefa 2: atualizar todos os agent JSONs do Kiro - registrar o novo hook

**Arquivos:**
- Modify: `.kiro/agents/default.json`
- Modify: `.kiro/agents/reviewer.json`
- Modify: `.kiro/agents/researcher.json`

No array `preToolUse` de cada agent, adicionar duas entradas:
```json
{"matcher": "fs_write", "command": "hooks/security/block-outside-workspace.sh"},
{"matcher": "execute_bash", "command": "hooks/security/block-outside-workspace.sh"}
```

default.json ja tem matcher `fs_write` (pre-write.sh); o novo hook entra antes (primeiro a checagem de seguranca, depois o workflow gate).
reviewer/researcher nao tinham matcher fs_write antes, entao basta adicionar.

**Verificação:** `jq '.hooks.preToolUse[] | select(.command | contains("block-outside-workspace"))' .kiro/agents/{default,reviewer,researcher}.json | jq -s 'length'` = 6 (2 entradas por agent x 3 agents)

### Tarefa 3: atualizar a configuracao do Claude Code - generate-platform-configs.sh

**Arquivos:**
- Modify: `scripts/generate-platform-configs.sh`

Na geracao de `.claude/settings.json`:
- No array de hooks do `PreToolUse` matcher Bash, adicionar `block-outside-workspace.sh`
- Adicionar novo `PreToolUse` matcher `Write|Edit` com `block-outside-workspace.sh` (antes de pre-write.sh)

Na geracao dos agents reviewer/researcher:
- No array `preToolUse`, adicionar as duas entradas de block-outside-workspace (fs_write + execute_bash)

**Verificação:** `bash scripts/generate-platform-configs.sh && grep -c 'block-outside-workspace' .claude/settings.json .kiro/agents/*.json` - .claude/settings.json >= 2; cada agent json >= 2

### Tarefa 4: testes manuais do hook

**Teste A: fs_write bloqueia caminho externo**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"/tmp/evil.txt","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Teste B: fs_write libera caminho dentro do workspace**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"hooks/test.txt","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 0, 无输出
```

**Teste C: bash bloqueia escrita externa**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello > ~/.zshrc"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Teste D: bash libera comando normal**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 0, 无输出
```

**Teste E: fs_write bloqueia path traversal**
```bash
echo '{"tool_name":"fs_write","tool_input":{"file_path":"../../../etc/passwd","command":"create"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Teste F: bash bloqueia redirect com append**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"echo data >> ~/evil.txt"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Teste G: bash bloqueia tar -C externo**
```bash
echo '{"tool_name":"execute_bash","tool_input":{"command":"tar -xf archive.tar -C /usr/local/"}}' | bash hooks/security/block-outside-workspace.sh
# 预期: exit 2, stderr 包含 "BLOCKED"
```

**Verificação:** os 4 testes passam

### Tarefa 5: registrar em knowledge

**Arquivos:**
- Modify: `knowledge/episodes.md`
- Modify: `knowledge/rules.md`

Em episodes.md, fazer append do registro desta implementacao.
Em rules.md, atualizar a regra existente, ou criar a regra de workspace boundary se nao existir.

**Verificação:** `grep -c 'workspace' knowledge/episodes.md` >= 1

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

The remaining issues are edge cases that would require sophisticated prompt injection to exploit. For the stated goal of preventing accidental agent missteps rather than defending against malicious attacks, this implementation provides sufficient protection.

#### Verdict: **APPROVE**

The plan now meets security requirements for preventing accidental agent writes outside workspace boundaries. The documented scope limitations (Decision 7) appropriately exclude OS-level attack vectors that belong in system sandboxing rather than application hooks.

## Checklist
- [x] `hooks/security/block-outside-workspace.sh` existe e e executavel
- [x] sintaxe do hook correta (`bash -n` passa)
- [x] fail-closed quando a deteccao de workspace falha (bloqueia toda escrita)
- [x] default.json preToolUse contem block-outside-workspace (2 entradas: fs_write + execute_bash)
- [x] reviewer.json preToolUse contem block-outside-workspace (2 entradas: fs_write + execute_bash)
- [x] researcher.json preToolUse contem block-outside-workspace (2 entradas: fs_write + execute_bash)
- [x] generate-platform-configs.sh inclui a configuracao de block-outside-workspace
- [x] `.claude/settings.json` apos a geracao contem block-outside-workspace
- [x] Teste A: fs_write com caminho externo bloqueado (exit 2)
- [x] Teste B: fs_write com caminho interno passa (exit 0)
- [x] Teste C: bash com escrita externa bloqueado (exit 2)
- [x] Teste D: bash com comando normal passa (exit 0)
- [x] Teste E: fs_write com path traversal bloqueado (exit 2)
- [x] Teste F: bash com append redirect bloqueado (exit 2)
- [x] Teste G: bash com tar -C externo bloqueado (exit 2)
- [x] knowledge atualizado
