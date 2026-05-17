# Enforcement de Checklist TDD - Qualidade do Plan + Integridade da Execução

**Objetivo:** Eliminar de forma codificada os tres problemas centrais (marcacao falsa em itens da checklist do plan, baixa cobertura, degradacao da capacidade do agent), entregando uma garantia de qualidade ponta a ponta dirigida por testes.
**Arquitetura:** Quatro camadas de protecao: (1) ao escrever o plan, um Static Rubric valida estrutura; (2) o prompt do reviewer e reforcado para auditar cobertura; (3) na execucao, hook intercepta marcacoes sem evidencia; (4) o Stop hook reexecuta todos os verify commands para a confirmacao final. Design central: cada item da checklist precisa ter um verify command executavel, e a marcacao depende do registro de uma execucao bem-sucedida desse comando.
**Tech Stack:** Shell (bash), jq, Markdown

## Key Decisions

1. **Formato do verify command**: `- [ ] descricao | \`verify command\``, com ` | \` ` separando descricao de comando, parsable por maquina e legivel para humano. Sem HTML comment (rules.md proibe HTML comment em arquivos de skill, manter consistencia)
2. **Mecanismo de registro de execucao**: hook PostToolUse de bash escreve, para cada comando, hash + exit code + timestamp em `/tmp/verify-log-<workspace-hash>.jsonl`. Ao marcar um item, o hook PreToolUse verifica se ha registro de sucesso para aquele verify command (exit 0, dentro de 10 minutos)
3. **Validacao de estrutura do plan via PreToolUse hook**: ao escrever em `docs/plans/*.md`, validar a estrutura (existir Task, Verify, Checklist); falha leva a exit 2 (bloqueio forte)
4. **Reforco do reviewer via prompt**: em reviewer-prompt.md, incluir requisito de auditoria de cobertura da checklist + requisito de propor cenarios adversariais
5. **Reforco do Stop hook**: verify-completion.sh nao apenas conta marcacoes; tambem extrai e reexecuta todos os verify commands; qualquer falha = nao concluido
6. **Sem forcar Red-Green**: pesquisa mostrou que este projeto e um framework de shell hooks (nao codigo de aplicacao); a maior parte dos verify e assertion via grep/jq, nao unit test; obrigar Red-Green adiciona muita complexidade com retorno baixo. Manter sugestao de TDD na planning skill, sem hook coercitivo
7. **Sem lock de arquivos de teste**: pelo mesmo motivo; o projeto nao tem arquivos de teste tradicionais; verify command vive dentro do plan
8. **~~Janela de 30 minutos~~ -> 10 minutos**: o reviewer apontou que 30 min permite resultado obsoleto; mudar para 10 min
9. **Append atomico no log**: usar `>>` (POSIX garante atomicidade para writes <=PIPE_BUF; uma linha JSON tem muito menos que 4096 bytes); flock nao e necessario
10. **Workspace hash de 8 caracteres**: e arquivo temporario por session, nao armazenamento permanente. A chance de duas pastas distintas colidirem na mesma maquina simultaneamente e baixa; mesmo se colidir, so adicionaria entradas irrelevantes sem afetar a corretude (a busca casa por cmd_hash exato)
11. **Sem normalizacao de comando**: o verify command e extraido literal do plan e gravado literal no log. O mesmo verify command tem uma unica forma no plan; nao ha conflito entre `echo "test"` e `echo 'test'`
12. **Limpeza automatica do log**: apos a execucao do stop hook do verify-completion, apagar o log do workspace atual
13. **Timeout no verify-completion**: para evitar loop infinito, cada comando recebe 30 segundos de timeout

## Tarefas

### Tarefa 1: criar o gravador de execucoes verify - post-bash-verify-log.sh

**Arquivos:**
- Modify: `hooks/feedback/post-write.sh` (incrementar o post-write existente com a logica de gravacao de execucao bash, mas o que de fato precisamos e PostToolUse[execute_bash], entao novo arquivo)
- Create: `hooks/feedback/post-bash.sh`

Hook PostToolUse[execute_bash] que, apos cada execucao bash, registra:
```jsonl
{"cmd_hash":"<sha1 of command>","cmd":"<command>","exit_code":0,"ts":1739612345}
```

Escreve em `/tmp/verify-log-<workspace-hash>.jsonl`.

Logica:
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

**Verificação:** `echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"},"tool_output":{"exit_code":"0"}}' | bash hooks/feedback/post-bash.sh && tail -1 /tmp/verify-log-*.jsonl | jq .cmd_hash` deve imprimir um hash nao vazio

### Tarefa 2: criar hook que intercepta marcacoes da checklist - gate-checklist-check.sh

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh` (incluir a logica de checagem de marcacao no pre-write existente)

Apos a funcao gate_check de pre-write.sh e antes de scan_content, incluir a interceptacao da marcacao:

Condicao: o alvo da escrita e `docs/plans/*.md` e o `new_str`/`content` contem `- [x]`

Logica:
1. Extrair, do conteudo gravado, todos os verify commands `- [x] ... | \`command\``
2. Para cada verify command, calcular cmd_hash; procurar no verify-log uma entrada exit_code=0 nos ultimos 30 minutos
3. Se algum verify command nao tem registro de sucesso -> exit 2 (bloqueio forte) com mensagem "Run the verify command first"
4. Se a linha `- [x]` nao tem verify command (sem o separador ` | \` `) -> exit 2 com mensagem "Checklist item missing verify command"

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
- Teste A: gravar plan com `- [x]` sem verify command -> exit 2
- Teste B: gravar plan com `- [x] ... | \`echo test\`` mas sem ter executado o comando -> exit 2
- Teste C: executar `echo test` antes (gera o registro no log) e depois gravar o `- [x]` correspondente -> exit 0 (libera)

### Tarefa 3: Static Rubric de estrutura do plan

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh`

Antes de gate_checklist, adicionar checagem de estrutura do plan (so para `docs/plans/*.md` em operacao create):

Itens validados:
1. precisa ter secao `## Tasks`
2. precisa ter secao `## Checklist`
3. precisa ter pelo menos um `### Task`
4. cada `### Task` precisa de uma linha `**Verify:**`
5. todo `- [ ]` em `## Checklist` precisa do verify command no formato ` | \`command\``
6. quantidade de itens da checklist >= numero de Tasks (cada task com ao menos um verify)

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
- Teste A: gravar plan sem `## Checklist` -> exit 2
- Teste B: gravar plan com itens da checklist sem verify command -> exit 2
- Teste C: gravar plan com estrutura completa -> exit 0

### Tarefa 4: reforcar o Stop hook verify-completion

**Arquivos:**
- Modify: `hooks/feedback/verify-completion.sh`

Apos a contagem de checklist atual, incluir a logica de reexecucao dos verify commands:

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

**Verificação:** construir um plan com `- [x] test | \`exit 1\``; o stop hook deve reportar verify failed

### Tarefa 5: reforcar o Reviewer prompt - cobertura + cenarios adversariais

**Arquivos:**
- Modify: `agents/reviewer-prompt.md`
- Modify: `skills/reviewing/SKILL.md`

No modo Plan Review de reviewer-prompt.md, adicionar:

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

### Tarefa 6: registrar o novo hook na configuracao dos agents

**Arquivos:**
- Modify: `.kiro/agents/default.json`
- Modify: `.kiro/agents/reviewer.json`
- Modify: `.kiro/agents/researcher.json`
- Modify: `scripts/generate-platform-configs.sh`

Adicionar PostToolUse[execute_bash] -> post-bash.sh em todos os agents.
pre-write.sh ja esta registrado, sem alteracoes adicionais (a logica nova fica dentro do hook existente).

**Verificação:** `jq '.hooks.postToolUse[] | select(.command | contains("post-bash"))' .kiro/agents/default.json` deve imprimir saida nao vazia

### Tarefa 7: atualizar a planning skill - novo formato de checklist

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

Atualizar a exigencia de formato da Checklist no template do plan:

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

### Tarefa 8: registrar em knowledge

**Arquivos:**
- Modify: `knowledge/episodes.md`
- Modify: `knowledge/rules.md`

Em episodes.md, fazer append do registro desta implementacao.
Em rules.md, na secao workflow, anotar: marcacao na checklist exige evidencia de execucao do verify command, com hook como obrigatorio.

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
- [x] post-bash.sh existe e registra execucoes bash em jsonl | `test -f hooks/feedback/post-bash.sh && bash -n hooks/feedback/post-bash.sh`
- [x] post-bash.sh grava cmd hash e exit code corretos | `echo '{"tool_name":"execute_bash","tool_input":{"command":"echo hello"},"tool_output":{"exit_code":"0"}}' | bash hooks/feedback/post-bash.sh && tail -1 /tmp/verify-log-*.jsonl | jq -e '.cmd_hash'`
- [x] pre-write.sh bloqueia marcacao na checklist sem verify command | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] done"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] pre-write.sh bloqueia marcacao na checklist sem registro de execucao | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] done | \`echo never_ran_this_xyz\`"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] pre-write.sh libera marcacao com registro de execucao | `echo test_verify_pass | shasum | cut -c1-40 | xargs -I{} sh -c 'echo "{\"cmd_hash\":\"{}\",\"cmd\":\"test_verify_pass\",\"exit_code\":0,\"ts\":$(date +%s)}" >> /tmp/verify-log-*.jsonl' && echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test.md","command":"str_replace","new_str":"- [x] pass | \`test_verify_pass\`"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 0`
- [x] estrutura do plan: ausencia de ## Checklist e bloqueada | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] estrutura do plan: item da checklist sem verify e bloqueado | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n## Checklist\n- [ ] item without verify\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 2`
- [x] estrutura do plan: plan completo e liberado | `echo '{"tool_name":"fs_write","tool_input":{"file_path":"docs/plans/test-struct.md","command":"create","file_text":"# Test\n## Tasks\n### Task 1\n**Verify:** cmd\n## Review\n## Checklist\n- [ ] item | \`echo ok\`\n"}}' | bash hooks/gate/pre-write.sh 2>&1; test $? -eq 0`
- [x] stop hook verify-completion reexecuta os verify commands | `grep -q 'VERIFY FAILED\|verify commands' hooks/feedback/verify-completion.sh`
- [x] reviewer prompt contem requisito de Checklist Coverage | `grep -c 'Checklist Coverage' agents/reviewer-prompt.md`
- [x] default.json contem hook post-bash | `jq -e '.hooks.postToolUse[] | select(.command | contains("post-bash"))' .kiro/agents/default.json`
- [x] planning skill explica o novo formato de checklist | `grep -c 'verify command' skills/planning/SKILL.md`
- [x] knowledge atualizada | `grep -c 'tdd-checklist' knowledge/episodes.md`
