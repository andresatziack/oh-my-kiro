# Reformulação da Knowledge Base - Arquitetura de Memória de Canal Duplo

**Objetivo:** Refatorar a knowledge base mista para uma arquitetura em duas camadas (rules + episodes), com captura automatica + manual em paralelo, evoluindo conhecimento de forma continua e trocando coercao por prompt por hook como restricao forte.

**Insight Central:** Comportamento sem hook que forca = nao acontece (validado em sed/JSON 10x). Captura, recall e governanca da knowledge base devem ser conduzidos por hook sempre que possivel.

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│                   落库（双通道）                       │
│                                                     │
│  自动通道 (hook)          人工通道 (@reflect)         │
│  简单纠正: 别用X/换成Y    复杂洞察: 人主动触发         │
│  ↓                       ↓                          │
│  4-Gate Pipeline         agent 辅助提炼              │
│  ↓                       ↓                          │
│  ┌─────────────────────────────────────┐            │
│  │         episodes.md (≤30条)          │            │
│  │  append-only, 去重, 实时计数         │            │
│  └──────────────┬──────────────────────┘            │
│                 │ ≥3次同类 → 晋升提醒                │
│  ┌──────────────▼──────────────────────┐            │
│  │         rules.md (≤30条 ≤2KB)       │            │
│  │  精炼可执行规则, hook 注入召回        │            │
│  └─────────────────────────────────────┘            │
│                                                     │
│  reference/  (不变, 手动维护的参考资料)               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   召回 (hook 驱动)                    │
│  会话首次 prompt → 注入 rules.md 前 10 条            │
│  有高频关键词(≥3次) → 一行晋升提醒                    │
│  有 health issues → 一行指针到报告文件                │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   治理 (自动+人工)                    │
│  自动: 去重 / 晋升标记 / 质量报告生成                 │
│  人工: 定期看报告 → 晋升 / 清理 / 调整               │
└─────────────────────────────────────────────────────┘
```

## Decisões

| # | Decisao | Motivo | Status |
|---|------|------|------|
| 1 | Duas camadas: rules.md + episodes.md + reference/ | Consenso da industria + validacao no projeto | ✅ |
| 2 | Captura em dois canais: hook automatico + @reflect manual | Automatico evita esquecimento; manual cobre insights complexos | ✅ |
| 3 | Captura automatica trata so padroes simples (nao use X / use Y) | Limites do regex em shell; melhor perder do que escrever lixo | ✅ |
| 4 | episodes.md e append-only; o hook nao apaga | Evitar problemas de portabilidade de sed -i entre plataformas | ✅ |
| 5 | Dedup com grep -c em tempo real, sem update in-place x N | Edicao in-place em shell e instavel | ✅ |
| 6 | Relatorio de qualidade vai para arquivo; o context recebe so um pointer de uma linha | Evitar saida frequente de Stop hook consumindo context | ✅ |
| 7 | Eliminacao por capacidade fica com humano/agent; hook so reporta | Hook so faz append, nunca delete: simples e seguro | ✅ |
| 8 | Pipeline de captura em script separado | context-enrichment.sh nao deve ficar pesado demais | ✅ |
| 9 | promote_candidate nao e armazenado; e calculado em runtime | Coerencia com a politica append-only; sem alterar status in-place | ✅ |
| 10 | keywords sao apenas termos tecnicos em ingles | grep -iw nao reconhece word boundary em chines | ✅ |
| 11 | auto-capture usa exit code para diferenciar resultados | Evitar lembrete de self-reflect mesmo apos a captura automatica | ✅ |

### Limitações Conhecidas
- Escrita concorrente: varios agents podem fazer append em episodes.md em paralelo, com competicao teorica; na escala atual (<=30 itens, baixa frequencia) e aceitavel

---

## Passos

### Tarefa 0: backup

```bash
cp knowledge/lessons-learned.md knowledge/lessons-learned.md.bak
git status --short knowledge/
```

### Tarefa 1: criar rules.md + episodes.md

**Arquivos:** Create `knowledge/rules.md`, `knowledge/episodes.md`; Delete `knowledge/lessons-learned.md`

**Step 1: destilar rules.md**

Extrair de Mistakes/Wins/Rules Extracted em lessons-learned.md, no formato:

```markdown
# Agent Rules (Semantic Memory)

> Distilled from repeated episodes. ≤30 rules, ≤2KB. Each rule: DO/DON'T + trigger.

1. JSON = jq，无条件无例外。禁止 sed/awk/grep 修改 JSON。[hook: block-sed-json]
2. macOS 用 stat -f，禁止 stat -c（GNU-only）。
3. grep -c 无匹配时 exit 1 但仍输出 0，不要和 || echo 0 组合。
4. shell 脚本生成前确认目标平台，BSD vs GNU 工具链差异。
5. 教训记录不等于修复。反复犯错（≥3次）→ 必须升级为 hook 拦截。
6. 收到任务第一步：读 context-enrichment 输出，按提示走，不跳过。
7. 重构时逐项检查旧能力是否被覆盖，不能只关注新增。
8. 非功能性需求（性能、可靠性、长时间运行）必须和功能性需求同等对待。
9. 方案 review 必须用真实场景 corner case 检验，不能只看 happy path。
10. Skill 文件不得包含 HTML 注释（防 prompt injection）。[hook: scan-skill-injection]
```

Cada rule precisa:
- Ter acao DO/DON'T explicita
- Maximo de 2 linhas
- Cenario de trigger
- Sem narrativa (a narrativa vai em episodes.md)
- Marcar `[hook: xxx]` se ja existir hook correspondente

**Step 2: criar episodes.md**

Refatorar o lessons-learned.md mesclando duplicatas; usar formato de linha amigavel a shell.

**Restricao de formato: o campo SUMMARY de cada entrada nao pode conter `|` (use `/` no lugar) para garantir que `cut -d'|'` funcione corretamente.**

```markdown
# Episodes (Episodic Memory)

> Timestamped events. ≤30 entries. Auto-captured by hook + manual via @reflect.

<!-- FORMAT: DATE | STATUS | KEYWORDS | SUMMARY -->
<!-- STATUS: active / resolved / promoted -->
<!-- Promotion candidates are computed at runtime (keyword freq ≥3), not stored -->

2026-02-13 | promoted | sed,json,jq | sed处理JSON→用jq，×10次，已建hook [hook: block-sed-json]
2026-02-13 | promoted | stat,macos,bsd | macOS用stat-c→用stat-f，×3次
2026-02-13 | promoted | grep,exit-code | grep-c无匹配exit1但输出0
2026-02-14 | active | context-enrichment,soft-prompt | 软提醒被无视，需升级为MANDATORY
2026-02-14 | active | reviewer,skip | 写完plan跳过reviewer，无hook=跳过
2026-02-14 | resolved | skill-chain,skip | 跳过skill-chain直接写代码 [hook: enforce-skill-chain]
```

**Step 3: apagar arquivo antigo**

```bash
rm knowledge/lessons-learned.md
```

**Step 4: validacao**

```bash
wc -c knowledge/rules.md                                          # ≤2048
grep -c '^[0-9]' knowledge/rules.md                                # ≤30
grep -c '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} |' knowledge/episodes.md  # ≤30
test ! -f knowledge/lessons-learned.md && echo "DELETED"
```

### Tarefa 2: pipeline de captura automatica (hook)

**Arquivos:** Create `hooks/feedback/auto-capture.sh`; Modify `hooks/feedback/context-enrichment.sh`

**Step 1: criar auto-capture.sh**

Script independente, chamado por context-enrichment.sh apos detectar correction.

```bash
#!/bin/bash
# auto-capture.sh — 自动落库 pipeline
# 输入: $1 = 用户消息
# 输出: stdout 给 context-enrichment 转发给 agent
# Exit codes: 0 = 已捕获或已存在(不需要self-reflect), 1 = 被过滤(可能需要self-reflect)

USER_MSG="$1"
EPISODES="knowledge/episodes.md"
RULES="knowledge/rules.md"
DATE=$(date +%Y-%m-%d)
DATE_PATTERN='[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} |'

# ── Pre-check: episodes.md must exist (Task 1 creates it) ──
[ ! -f "$EPISODES" ] && exit 1

# ── Gate 1: 过滤低价值 ──
# 问句 → 丢弃
echo "$USER_MSG" | grep -qE '[？?][[:space:]]*$' && exit 1
# 无明确动作 → 丢弃
HAS_ACTION=$(echo "$USER_MSG" | grep -cE '(别用|不要用|换成|改成|禁止|必须|用.{1,10}不要|always|never|don.t|must|use .+ not|stop using)' || true)
[ "$HAS_ACTION" -eq 0 ] && exit 1
# 有明确动作的不受长度限制（Gate 1 只过滤无动作和问句）

# ── Gate 2: 提取关键词（仅英文技术术语，≥4字符）──
# head -3 取消息中最先出现的3个术语（出现越早越可能是核心词）
KEYWORDS=$(echo "$USER_MSG" | grep -oE '[a-zA-Z_][a-zA-Z0-9_-]{3,}' | grep -viE '^(this|that|with|from|have|been|your|what|when|should|always|never|dont|must|stop|using|every|about|just|like|make|more|than|them|they|these|those|very|will|would|could|also|into|only|some|such|each|other|after|before|because|between|during|without)$' | awk '!seen[$0]++' | head -3 | tr '\n' ',' | sed 's/,$//')
# 无有效关键词 → 丢弃
[ -z "$KEYWORDS" ] && exit 1

# ── Gate 3: 去重 ──
KEYWORD_PATTERN=$(echo "$KEYWORDS" | tr ',' '|')

# 已在 rules.md → 跳过（已有规则覆盖）
if grep -qiwE "$KEYWORD_PATTERN" "$RULES" 2>/dev/null; then
  echo "📚 Already in rules.md — skipping capture."
  exit 0
fi

# 已在 episodes.md → 跳过写入，检查晋升（实时计数，不存储 promote_candidate）
MATCH_COUNT=$(grep -ciwE "$KEYWORD_PATTERN" "$EPISODES" 2>/dev/null || echo 0)
if [ "$MATCH_COUNT" -gt 0 ]; then
  if [ "$MATCH_COUNT" -ge 2 ]; then
    echo "🔥 Similar pattern ×$((MATCH_COUNT+1)) in episodes. Consider promoting to rules.md or creating a hook."
  else
    echo "📚 Similar episode exists — skipping duplicate."
  fi
  exit 0
fi

# ── Gate 4: 容量检查 ──
EPISODE_COUNT=$(grep -c "$DATE_PATTERN" "$EPISODES" 2>/dev/null || echo 0)
if [ "$EPISODE_COUNT" -ge 30 ]; then
  echo "⚠️ episodes.md at capacity (30/30). New episode NOT captured. Review .health-report.md."
  exit 0
fi

# ── 写入 ──
SUMMARY=$(echo "$USER_MSG" | head -c 80 | tr '|' '/' | tr '\n' ' ')
echo "$DATE | active | $KEYWORDS | $SUMMARY" >> "$EPISODES"
echo "📝 Auto-captured → episodes.md: '$SUMMARY'"

# ── 标记知识库变更（供 Stop hook 质量报告用）──
touch "/tmp/kb-changed-$(pwd | shasum 2>/dev/null | cut -c1-8 || echo default).flag"
exit 0
```

**Step 2: alterar context-enrichment.sh**

Apos detectar correction, chamar auto-capture.sh:

```bash
if [ "$DETECTED" -eq 1 ]; then
  # 自动落库（exit 0=已处理, exit 1=被过滤需要 self-reflect）
  bash "$(dirname "$0")/auto-capture.sh" "$USER_MSG"
  if [ $? -eq 1 ]; then
    # 被过滤 = 复杂洞察，提醒 agent 用 self-reflect 或人用 @reflect
    echo "🚨 CORRECTION DETECTED (complex). Use self-reflect skill or @reflect to capture."
  fi
fi
```

A injecao de rules.md passa a ser dinamica:

```bash
LESSONS_FLAG="/tmp/lessons-injected-$(pwd | shasum 2>/dev/null | cut -c1-8 || echo default).flag"
if [ ! -f "$LESSONS_FLAG" ]; then
  if [ -f "knowledge/rules.md" ]; then
    echo "📚 AGENT RULES (from knowledge/rules.md):"
    grep '^[0-9]' "knowledge/rules.md" | head -10
  else
    # fallback 硬编码
    cat << 'FALLBACK'
📚 AGENT RULES (fallback):
  • JSON = jq, 无条件无例外。
  • macOS 用 stat -f, 禁止 stat -c。
FALLBACK
  fi
  # 晋升候选提醒（实时计算，不依赖存储的 promote_candidate 状态）
  if [ -f "knowledge/episodes.md" ]; then
    PROMOTE=$(grep '| active |' "knowledge/episodes.md" 2>/dev/null | cut -d'|' -f3 | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort | uniq -c | awk '$1 >= 3' | wc -l | tr -d ' ')
    [ "$PROMOTE" -gt 0 ] && echo "⬆️ $PROMOTE keyword patterns appear ≥3 times in episodes → consider promotion"
  fi
  # 质量报告提醒
  if [ -f "knowledge/.health-report.md" ]; then
    ISSUES=$(grep -cE '⬆️|⚠️|🧹' "knowledge/.health-report.md" 2>/dev/null || true)
    [ "$ISSUES" -gt 0 ] && echo "📊 KB has $ISSUES issues → knowledge/.health-report.md"
  fi
  touch "$LESSONS_FLAG"
fi
```

**Step 3: validacao**

```bash
# 模拟纠正消息测试 pipeline
echo '别用sed处理JSON，用jq' | bash hooks/feedback/auto-capture.sh "别用sed处理JSON，用jq"
cat knowledge/episodes.md | tail -1
```

### Tarefa 3: relatorio de saude

**Arquivos:** Create `hooks/feedback/kb-health-report.sh`; Modify Stop hook

**Step 1: criar kb-health-report.sh**

```bash
#!/bin/bash
# kb-health-report.sh — 生成知识库质量报告
# 触发条件: kb-changed flag 存在
# 输出: knowledge/.health-report.md (文件), stdout 一行摘要

KB_FLAG="/tmp/kb-changed-$(pwd | shasum 2>/dev/null | cut -c1-8 || echo default).flag"
COOLDOWN="/tmp/kb-report-$(pwd | shasum 2>/dev/null | cut -c1-8 || echo default).cooldown"

# 条件1: 有变更
[ ! -f "$KB_FLAG" ] && exit 0
rm "$KB_FLAG"

# 条件2: 本会话未报告过
[ -f "$COOLDOWN" ] && exit 0

EPISODES="knowledge/episodes.md"
RULES="knowledge/rules.md"
REPORT="knowledge/.health-report.md"
DATE_PATTERN='[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} |'

EPISODE_COUNT=$(grep -c "$DATE_PATTERN" "$EPISODES" 2>/dev/null || echo 0)
RULE_COUNT=$(grep -c '^[0-9]' "$RULES" 2>/dev/null || echo 0)
RULES_SIZE=$(wc -c < "$RULES" 2>/dev/null | tr -d ' ' || echo 0)
ACTIVE_COUNT=$(grep -c '| active |' "$EPISODES" 2>/dev/null || echo 0)
RESOLVED_COUNT=$(grep -c '| resolved |' "$EPISODES" 2>/dev/null || echo 0)
PROMOTED_COUNT=$(grep -c '| promoted |' "$EPISODES" 2>/dev/null || echo 0)

# 晋升候选：实时计算（提取所有 keywords，找出现 ≥3 次的）
PROMOTE_KEYWORDS=""
if [ -f "$EPISODES" ]; then
  # 提取所有 active episode 的 keywords 列，统计每个关键词出现次数
  PROMOTE_KEYWORDS=$(grep '| active |' "$EPISODES" 2>/dev/null | cut -d'|' -f3 | tr ',' '\n' | sed 's/^ *//;s/ *$//' | sort | uniq -c | sort -rn | awk '$1 >= 3 {print $2 " (x" $1 ")"}')
fi
PROMOTE_COUNT=$(echo "$PROMOTE_KEYWORDS" | grep -c '.' 2>/dev/null || echo 0)

# 生成报告文件
cat > "$REPORT" << EOF
# KB Health Report (auto-generated)
Updated: $(date '+%Y-%m-%d %H:%M')

## Status
- rules.md: ${RULE_COUNT}/30 (${RULES_SIZE}B/2048B)
- episodes.md: ${EPISODE_COUNT}/30 (active:${ACTIVE_COUNT} resolved:${RESOLVED_COUNT} promoted:${PROMOTED_COUNT})
- promote candidates: ${PROMOTE_COUNT}

## Actions Needed
EOF

ISSUES=0

if [ "$PROMOTE_COUNT" -gt 0 ]; then
  echo "$PROMOTE_KEYWORDS" | while IFS= read -r kw; do
    [ -n "$kw" ] && echo "- ⬆️ Promote: keyword '$kw' appears ≥3 times in active episodes" >> "$REPORT"
  done
  ISSUES=$((ISSUES + PROMOTE_COUNT))
fi

if [ "$EPISODE_COUNT" -ge 25 ]; then
  echo "- ⚠️ episodes.md nearing cap: ${EPISODE_COUNT}/30" >> "$REPORT"
  ISSUES=$((ISSUES + 1))
fi

if [ "$RESOLVED_COUNT" -gt 10 ]; then
  echo "- 🧹 ${RESOLVED_COUNT} resolved episodes — consider purging" >> "$REPORT"
  ISSUES=$((ISSUES + 1))
fi

if [ "$RULES_SIZE" -gt 1800 ]; then
  echo "- 📏 rules.md approaching limit: ${RULES_SIZE}B/2048B" >> "$REPORT"
  ISSUES=$((ISSUES + 1))
fi

if [ "$ISSUES" -eq 0 ]; then
  echo "- ✅ No issues" >> "$REPORT"
fi

# stdout: 只在有问题时输出一行
if [ "$ISSUES" -gt 0 ]; then
  echo "📊 KB health: $ISSUES issues → knowledge/.health-report.md"
fi

touch "$COOLDOWN"
```

**Step 2: chamar do Stop hook**

```bash
bash "$(dirname "$0")/../feedback/kb-health-report.sh"
```

**Step 3: validacao**

```bash
touch "/tmp/kb-changed-$(pwd | shasum | cut -c1-8).flag"
bash hooks/feedback/kb-health-report.sh
cat knowledge/.health-report.md
```

### Tarefa 4: comando @reflect (canal manual de captura)

**Arquivos:** Create `.kiro/prompts/reflect.md` (Kiro) ou `.claude/commands/reflect.md` (CC)

**Step 1: criar o prompt reflect**

```markdown
# Reflect — Manual Knowledge Capture

Read the current conversation and identify insights worth preserving.

## Process
1. Ask user: "What insight should I capture?" (or user already stated it)
2. Extract: trigger scenario + DO/DON'T action + keywords
3. Check dedup: grep -iw keywords in knowledge/rules.md and knowledge/episodes.md
   - Already in rules → tell user, skip
   - Already in episodes → tell user count, suggest promotion if ≥3
4. Format: `DATE | active | KEYWORDS | SUMMARY` (≤80 chars, no | in summary)
5. Append to knowledge/episodes.md
6. Output: 📝 Captured → episodes.md: 'SUMMARY'

## Rules
- @reflect only writes to episodes.md (promotion to rules.md is done by self-reflect skill, not @reflect)
- Summary must contain actionable DO/DON'T, not narrative
- Keywords: 1-3 terms, ≥4 chars each, comma-separated
- If episodes.md has ≥30 entries, warn user to clean up first
```

**Step 2: validacao**

```bash
# Kiro
test -f .kiro/prompts/reflect.md && echo "EXISTS"
# CC
test -f .claude/commands/reflect.md && echo "EXISTS"
```

### Tarefa 5: simplificar a self-reflect skill

**Arquivos:** Modify `skills/self-reflect/SKILL.md`

Restringir a responsabilidade a dois cenarios:

```markdown
## Scope (v3)

1. **Promotion execution**: When hook outputs 🔥 or ⬆️, read episodes.md,
   distill into 1-2 line rule, propose to user, write to rules.md if approved.
   Mark source episodes as `promoted`.

2. **Complex insight capture**: When hook outputs 🚨 and the correction is
   too complex for auto-capture (no simple DO/DON'T pattern), help user
   articulate and write to episodes.md via the same format.

NOT responsible for: daily capture (hook does it), dedup (hook does it),
quality reporting (hook does it).
```

Atualizar a tabela Sync Targets:

```markdown
## Sync Targets

| Scenario | Target |
|----------|--------|
| Promotion (≥3 same pattern) | knowledge/rules.md |
| Complex insight | knowledge/episodes.md |
| Code-enforceable rule | .kiro/rules/enforcement.md |
```

### Tarefa 6: atualizar INDEX.md, AGENTS.md e referencias globais

**Arquivos:** Modify `knowledge/INDEX.md`, `AGENTS.md`, limpar referencias por grep no projeto inteiro

**Step 1: INDEX.md**

```markdown
## Routing Table

| Question Type | Jump To | Example |
|---|---|---|
| Agent rules & constraints | knowledge/rules.md | "JSON 用什么工具？" |
| Past incidents & events | knowledge/episodes.md | "这个错误以前犯过吗？" |
| KB health & cleanup | knowledge/.health-report.md | "知识库状态？" |
| Reference materials | knowledge/reference/ | "Mermaid 语法？" |
```

**Step 2: AGENTS.md**

Atualizar a secao Knowledge Retrieval:
```markdown
## Knowledge Retrieval
- rules.md 由 hook 自动注入（会话首次 prompt）
- 复杂问题 → knowledge/INDEX.md → source docs
- **必须引用来源文件**，不引用 = 幻觉

## Self-Learning
- 简单纠正 → hook 自动捕获到 episodes.md
- 复杂洞察 → @reflect 人工落库
- 晋升提醒（🔥/⬆️）→ self-reflect skill 执行
```

**Step 3: limpar referencias globais**

```bash
grep -r 'lessons-learned' . --include='*.md' --include='*.sh' | grep -v '.git' | grep -v '.bak' | grep -v 'archive/'
# 将所有引用更新为 rules.md 或 episodes.md
```

**Step 4: validacao**

```bash
grep -r 'lessons-learned' . --include='*.md' --include='*.sh' | grep -v '.git' | grep -v '.bak' | grep -v 'archive/' || echo "CLEAN"
```

---

## Review

### Strengths
- **Dois canais complementares**: hook automatico evita esquecimento, @reflect manual cobre insights complexos
- **Conduzido por hooks**: captura, recall e relatorio sao garantidos pelo hook, sem depender da iniciativa do agent
- **Controle de qualidade no momento da captura**: 4-Gate pipeline filtra de baixo valor, dedup e capacidade
- **Governanca pos-fato sem atrito**: relatorio de qualidade vai para arquivo, e o context recebe so um pointer; basta ler o relatorio para saber o que fazer
- **Operacao shell simples e estavel**: append-only, sem alteracao in-place; sem sed -i cross-platform
- **Custo de context controlado**: rules so injeta na primeira vez, relatorio so um pointer, lembrete de promotion em uma linha
- **Distincao por exit code**: auto-capture sucesso vs filtrada, evitando lembrete redundante de self-reflect
- **Promotion calculado em runtime**: nao armazena promote_candidate, alinhado ao append-only

### Risks & Mitigations
- **Captura automatica gera lixo**: Gate 1 filtra com rigor (perguntas/sem acao -> descartar); itens com acao explicita nao tem limite de tamanho; SUMMARY truncado em 80 caracteres
- **Falso positivo do grep para keywords**: apenas termos tecnicos em ingles >= 4 caracteres + grep -iw (word boundary)
- **Formato de episodes.md corrompido**: trocar `|` por `/` no texto do usuario; formato em linha em vez de tabela
- **Estouro de capacidade**: ao chegar em 30, recusa novas escritas + lembrete via relatorio; sem deletes automaticos
- **Esquecer de usar @reflect**: aceitavel - insights complexos sao raros; o canal automatico cobre o de alta frequencia
- **Escrita concorrente**: append simultaneo de varios agents tem competicao teorica; na escala atual e aceitavel

### Verdict: **APPROVED**

## Checklist

- [ ] knowledge/lessons-learned.md.bak backup criado
- [ ] knowledge/rules.md criado, <=2KB, <=30 entradas, cada uma com DO/DON'T + cenario
- [ ] knowledge/episodes.md criado, formato em linha (sem tabela), duplicatas mescladas, com coluna status
- [ ] hooks/feedback/auto-capture.sh criado, 4-Gate pipeline, exit 0/1 distintos
- [ ] auto-capture Gate 1: descartar perguntas; descartar sem acao (com acao nao tem limite de tamanho; SUMMARY truncado em 80 caracteres)
- [ ] auto-capture pre-check: episodes.md ausente leva a exit 1
- [ ] auto-capture Gate 2: apenas termos tecnicos em ingles >=4 caracteres; excluir palavras comuns
- [ ] auto-capture Gate 3: dedup com grep -iwE; promotion via grep -c em tempo real
- [ ] auto-capture Gate 4: capacidade >=30 recusa nova escrita
- [ ] context-enrichment.sh decide o lembrete de self-reflect via exit code do auto-capture
- [ ] context-enrichment.sh le rules.md dinamicamente, com fallback hardcoded
- [ ] context-enrichment.sh ao iniciar a session calcula promotion candidates em tempo real (frequencia >=3)
- [ ] context-enrichment.sh ao iniciar a session checa se .health-report.md tem issues
- [ ] hooks/feedback/kb-health-report.sh criado, com tres condicoes para disparar (mudanca + ha problema + primeira vez)
- [ ] kb-health-report calcula candidates em tempo real, sem depender de status armazenado
- [ ] kb-health-report usa o pattern de data `[0-9]{4}-[0-9]{2}-[0-9]{2} |` em vez de `^20`
- [ ] Stop hook chama kb-health-report.sh
- [ ] knowledge/.health-report.md gerado automaticamente; context recebe so um pointer
- [ ] prompt @reflect criado (.kiro/prompts/ e/ou .claude/commands/)
- [ ] SKILL.md de self-reflect simplificado (so executa promotion + ajuda em insight complexo)
- [ ] tabela de routing em knowledge/INDEX.md atualizada
- [ ] AGENTS.md atualizado (descricao dos dois canais)
- [ ] grep -r 'lessons-learned' no projeto sem residuos (excluindo .bak e archive/)
- [ ] teste simulado: correction simples -> auto-capture exit 0 -> nova entrada em episodes.md
- [ ] teste simulado: correction complexa -> auto-capture exit 1 -> lembrete de self-reflect
- [ ] teste simulado: correction repetida -> dedup, salta; >=3 vezes -> imprime 🔥 com lembrete de promotion
- [ ] teste simulado: kb-health-report gerado corretamente; promotion candidates calculados via frequencia de keywords
