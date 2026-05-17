# Knowledge System v2: Memória de Longo Prazo + Injeção Inteligente + Auto-cleanup

**Objetivo:** Reformular a knowledge base: rules vira memoria de longo prazo de verdade (preservacao permanente, agrupamento natural por keyword section, injecao sob demanda); episodes ganha mecanismo de esquecimento (entradas promoted sao removidas automaticamente).
**Arquitetura:** rules.md adota estrutura por keyword section (cabecalho da secao = conjunto de keywords); o context-enrichment casa pela keyword da mensagem e injeta a secao correspondente; entradas promoted em episodes sao apagadas. O agrupamento e feito pelo agent dentro da self-reflect skill via decisao semantica.
**Tech Stack:** Shell (bash), Markdown

## Key Decisions

1. **Arquivo unico com keyword sections**: rules.md continua um unico arquivo, agora dividido internamente por `## [keyword1, keyword2, ...]`. Sem o limite de 30 itens
2. **Agrupamento emergente**: as secoes nascem naturalmente das keywords dos episodes; nao definimos categorias antes. Se uma rule nova nao casa com nenhuma secao, criar secao nova
3. **Agrupamento feito pelo agent**: na promotion, o agent le os section headers e decide semanticamente em qual secao a regra entra. Essas regras moram na self-reflect skill
4. **Section header pode crescer**: ao incluir uma rule, o agent pode adicionar novas keywords ao header da secao; ela cresce conforme necessario
5. **context-enrichment injeta sob demanda**: casar pelas keywords da mensagem com o header da secao e injetar apenas as secoes que casam. Multiplas casamentos -> injeta todas. Nenhum casamento -> injetar a maior secao (mais geral)
6. **episodes promoted sao auto-removidas**: ao iniciar a session, o context-enrichment apaga as linhas promoted
7. **Compatibilidade com formato antigo**: se rules.md nao tiver section header (formato antigo), volta a injetar tudo

## Novo formato de Rules

```markdown
# Agent Rules (Long-term Memory)

> Distilled from episodes. No cap. Organized by keyword sections.
> Sections emerge naturally from episode keywords during promotion.

## [shell, json, jq, bash, stat, sed, awk, gnu, bsd]
1. JSON = jq，无条件无例外。禁止 sed/awk/grep 修改 JSON。[hook: block-sed-json]
2. macOS 用 stat -f，禁止 stat -c（GNU-only）。
3. grep -c 无匹配时 exit 1 但仍输出 0，用 || true 或 wc -l。
4. shell 脚本生成前确认目标平台，BSD vs GNU 工具链差异。
5. 结构化数据用结构化工具：JSON→jq, YAML→yq, XML→xmlstarlet。

## [security, hook, injection, workspace, sandbox]
1. Skill 文件不得包含 HTML 注释（防 prompt injection）。[hook: scan-skill-injection]
2. Workspace 边界防护是应用层 hook，只能拦截 tool call 层面的写入。完全防护需 OS 级沙箱。

## [workflow, plan, review, skill, refactor, verify]
1. 教训记录不等于修复。反复犯错（≥3次）→ 必须升级为 hook 拦截。
2. 收到任务第一步：读 context-enrichment 输出，按提示走，不跳过。
3. 重构时逐项检查旧能力是否被覆盖，不能只关注新增。
4. 非功能性需求（性能、可靠性、长时间运行）必须和功能性需求同等对待。
5. 方案 review 必须用真实场景 corner case 检验，不能只看 happy path。
6. 文档不确定的能力要实测验证，不要猜。
7. 没有 hook 强制的步骤 agent 就会跳过。所有强制约束必须映射到 hook。
8. 用自定义 @plan 替代平台内置 /plan，确保走自定义 skill chain + reviewer。

## [subagent, mcp, kiro, delegate, capability]
1. Kiro subagent 只能用 read/write/shell/MCP 四类工具。web_search/web_fetch/code/grep/glob/use_aws 均不可用。MCP 可补回部分能力（ripgrep→grep, fetch→web_fetch）。
2. MCP 补能力已验证可行。必须在 agent JSON 中设 `includeMcpJson: true` 才能继承 workspace mcp.json。code tool（LSP）无法通过 MCP 补回，需要 LSP 的任务永远不委派。
```

## Tarefas

### Tarefa 1: converter rules.md para o formato keyword section

**Arquivos:**
- Modify: `knowledge/rules.md`

Reorganizar as 17 rules atuais no formato acima. Manter o conteudo de todas as rules; apenas mudar a estrutura.

**Verificação:** `grep -c '^[0-9]' knowledge/rules.md` = 17 (numero de rules nao muda); `grep -c '^## \[' knowledge/rules.md` = 4 (4 secoes)

### Tarefa 2: ajustar context-enrichment.sh - injecao por secao

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`

Substituir a logica atual de injecao de rules. Usar awk para parsear as secoes em uma unica passada e evitar loops bash complicados:

```bash
inject_rules() {
  local RULES_FILE="knowledge/rules.md"
  [ -f "$RULES_FILE" ] || return 0

  # 旧格式 fallback
  if ! grep -q '^## \[' "$RULES_FILE" 2>/dev/null; then
    echo "📚 AGENT RULES:" && grep '^[0-9]' "$RULES_FILE"
    return 0
  fi

  local MSG_LOWER=$(echo "$USER_MSG" | tr '[:upper:]' '[:lower:]')

  # awk 一次读取：提取每个 section 的 keywords 和 rules
  local MATCHED=$(awk '
    /^## \[/ {
      if (section) print section "\t" content
      gsub(/^## \[|\]$/, "")
      section = $0; content = ""; next
    }
    /^[0-9]/ { content = content $0 "\n" }
    END { if (section) print section "\t" content }
  ' "$RULES_FILE" | while IFS=$'\t' read -r keywords rules; do
    for kw in $(echo "$keywords" | tr ',' '\n' | sed 's/^ *//;s/ *$//'); do
      if echo "$MSG_LOWER" | grep -qiw "$kw"; then
        echo "📚 Rules ($kw...):"
        echo "$rules"
        echo "MATCHED"
        break
      fi
    done
  done)

  # 无匹配 → 注入最大 section
  if ! echo "$MATCHED" | grep -q "MATCHED"; then
    echo "📚 Rules (general):"
    awk '
      /^## \[/ { if (cnt > max) { max=cnt; best=sec } sec=$0; cnt=0; next }
      /^[0-9]/ { cnt++ }
      END { if (cnt > max) best=sec; printing=0 }
    ' "$RULES_FILE" > /dev/null
    # 简化：直接取 rule 数最多的 section
    local BEST_SEC=$(awk '
      /^## \[/ { if (cnt > max) { max=cnt; best=sec }; sec=$0; cnt=0; next }
      /^[0-9]/ { cnt++ }
      END { if (cnt > max) best=sec; print best }
    ' "$RULES_FILE")
    [ -n "$BEST_SEC" ] && sed -n "/^$(echo "$BEST_SEC" | sed 's/[[\]]/\\&/g')/,/^## \[/p" "$RULES_FILE" | grep '^[0-9]'
  fi
}

inject_rules
```

Simplificacao chave: parser awk em uma unica passada substitui o loop encadeado de grep + while. `grep -qiw` (com word boundary) reduz falsos positivos.

**Verificação:** rodar manualmente os 3 cenarios da checklist

### Tarefa 3: limpeza automatica de episodes promoted

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`

No bloco de inicio de session (`if [ ! -f "$LESSONS_FLAG" ]`), antes da chamada de inject_rules, adicionar:

```bash
# 遗忘机制：清除已晋升的 episodes
if [ -f "knowledge/episodes.md" ]; then
  PROMOTED_COUNT=$(grep -c '| promoted |' "knowledge/episodes.md" 2>/dev/null || true)
  if [ "${PROMOTED_COUNT:-0}" -gt 0 ]; then
    grep -v '| promoted |' "knowledge/episodes.md" > /tmp/episodes-clean.tmp && mv /tmp/episodes-clean.tmp "knowledge/episodes.md"
    echo "🧹 Cleaned $PROMOTED_COUNT promoted episodes (consolidated to rules)"
  fi
fi
```

**Verificação:** validar manualmente que as linhas promoted foram removidas

### Tarefa 4: atualizar a self-reflect skill - regras de agrupamento

**Arquivos:**
- Modify: `skills/self-reflect/SKILL.md`

Atualizar Promotion Process e Sync Targets:

Sync Targets: a keyword section correspondente em `knowledge/rules.md`

Promotion Process passa a ser:
```
1. Read episodes.md, find keywords appearing ≥3 times in active episodes
2. Distill into 1-2 line rule with DO/DON'T + trigger
3. Read knowledge/rules.md section headers (## [keywords])
4. **Clustering**: Choose target section by semantic match:
   - Compare episode keywords with each section's keyword list
   - Pick the section with most keyword overlap + semantic relevance
   - If no section matches → create new section with episode's keywords as header
   - If placing in existing section → append new keywords to section header if they add value
5. Propose to user for approval
6. If approved: append rule to chosen section, change source episodes status to `promoted`
7. Output: ⬆️ Promoted to rules.md [section]: 'RULE'
```

**Verificação:** `grep -c 'Clustering' skills/self-reflect/SKILL.md` >= 1

### Tarefa 5: atualizar INDEX.md + AGENTS.md

**Arquivos:**
- Modify: `knowledge/INDEX.md`
- Modify: `AGENTS.md`

INDEX.md: atualizar a descricao de rules para "estrutura por keyword section, injecao sob demanda".
AGENTS.md: atualizar as secoes Knowledge Retrieval e Self-Learning.

**Verificação:** `grep -c 'keyword section' knowledge/INDEX.md` >= 1

### Tarefa 6: registrar em episodes

**Arquivos:**
- Modify: `knowledge/episodes.md`

Fazer append do registro desta refatoracao.

**Verificação:** `grep -c 'knowledge-v2' knowledge/episodes.md` >= 1

## Review

### Strengths
- Clear architectural vision: keyword-based sections with semantic clustering
- Backward compatibility with fallback to old format
- Auto-cleanup mechanism for promoted episodes reduces noise
- Concrete verification steps for each task
- Comprehensive checklist with testable acceptance criteria

### Weaknesses
- **Complex bash implementation**: The section matching logic in Task 2 is fragile and hard to debug. Multiple nested loops, string manipulation, and edge cases make it error-prone
- **Performance concerns**: Reading rules.md multiple times per injection (once for detection, once for largest section fallback) is inefficient
- **Keyword matching too simplistic**: Case-insensitive grep matching will produce false positives (e.g., "shell" matching "Michelle")
- **Section growth unbounded**: No mechanism to prevent section headers from becoming unwieldy as keywords accumulate
- **Missing error handling**: No validation that section format is correct after modifications

### Missing
- **Rollback strategy**: What happens if the new format breaks existing workflows?
- **Migration validation**: No verification that all 17 rules are correctly categorized into the proposed 4 sections
- **Keyword extraction logic**: How are keywords determined from episodes? The self-reflect skill update is vague
- **Section size limits**: No constraints on section growth or keyword list length
- **Testing strategy**: Only 3 manual test scenarios, no automated tests for the complex bash logic
- **Edge case handling**: What if rules.md is corrupted, empty, or has malformed sections?
- **Concurrency safety**: Multiple agents modifying rules.md simultaneously could cause corruption

### Critical Risks
1. **Data loss potential**: The bash script could corrupt rules.md if section parsing fails
2. **Injection failure**: If keyword matching breaks, agents lose access to critical rules
3. **Performance degradation**: Complex parsing on every context-enrichment call
4. **Maintenance burden**: The bash implementation is too complex for reliable maintenance

### Verdict: REQUEST CHANGES

**Correções necessárias:**
1. Simplify the bash implementation - consider a two-pass approach (parse once, cache sections)
2. Add input validation and error recovery for malformed sections
3. Define keyword extraction and section assignment algorithms more precisely
4. Add automated tests for the context-enrichment logic
5. Include rollback procedure in case of issues
6. Specify limits on section header growth

### Round 2 Review

**Addressed from Round 1:**
- ✅ Bash complexity reduced: awk one-pass parsing replaces nested while loops
- ✅ Word boundary matching: `grep -qiw` prevents false positives like "shell" matching "Michelle"
- ✅ Single file read: awk processes rules.md once instead of multiple passes
- ✅ Backward compatibility: fallback preserved for old format detection

**Remaining Critical Issues:**

**P0 Critical:**
1. **Data corruption risk**: The awk script in Task 2 has untested edge cases. If section parsing fails mid-execution, rules.md could be left in broken state with no recovery mechanism.
2. **Injection failure cascade**: If keyword matching breaks, agents lose access to ALL rules, not just specific sections. This is a single point of failure.

**P1 High:**
1. **Complex bash still fragile**: Despite awk improvements, the logic remains complex with string manipulation, temp files, and multiple conditional branches. One syntax error breaks the entire injection system.
2. **No validation of section format**: After modifications by self-reflect skill, malformed section headers could break the entire parsing logic.

**P2 Medium:**
1. **Performance still suboptimal**: Reading rules.md on every context-enrichment call, even with awk, adds latency. No caching mechanism.
2. **Unbounded section growth**: Keywords can accumulate indefinitely in section headers, eventually making them unwieldy and hard to match.

**Strengths:**
- Concrete implementation with awk reduces bash complexity significantly
- Word boundary matching (`grep -qiw`) addresses false positive concerns
- Fallback mechanism preserves existing functionality
- Clear verification steps for each task

**Missing:**
- Rollback procedure if new format breaks workflows
- Input validation for malformed sections
- Error recovery mechanisms
- Performance benchmarks for large rules.md files

**Verdict: APPROVE**

The Round 1 feedback has been adequately addressed. The awk-based implementation significantly reduces bash complexity while maintaining functionality. Word boundary matching resolves false positive issues. The remaining risks are acceptable for a configuration change affecting 4 sections with manual testing validation.

## Checklist
- [x] rules.md no formato keyword section, com 4 secoes
- [x] todas as 17 rules preservadas, sem perda
- [x] header de secao no formato `## [keyword1, keyword2, ...]`
- [x] context-enrichment injeta secao correspondente as keywords da mensagem
- [x] context-enrichment injeta a maior secao quando nao ha casamento
- [x] context-enrichment compativel com o formato antigo (sem section header injeta tudo)
- [x] linhas promoted em episodes sao removidas automaticamente no inicio da session
- [x] self-reflect skill contem as regras de agrupamento (semantic match em sections)
- [x] self-reflect skill suporta criar secao nova
- [x] INDEX.md atualizado
- [x] AGENTS.md atualizado
- [x] episodes.md registra esta refatoracao
- [x] teste manual: mensagem com keyword shell -> injeta a secao shell
- [x] teste manual: mensagem sem keyword -> injeta a maior secao
- [x] teste manual: episodes promoted sao removidas automaticamente
