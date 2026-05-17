# Reformulação da Knowledge Base - Arquitetura de Memória de Canal Duplo

**Objetivo:** 将混合知识库重构为 rules + episodes 双层结构，通过自动落库 + 人工落库双通道实现知识持续演进，用 hook 硬约束替代 prompt 软约束。

**Insight Central:** 没有 hook 强制的行为 = 不会发生（sed/JSON ×10 验证）。知识库的落库、召回、治理必须尽可能由 hook 驱动。

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

| # | 决策 | 原因 | 状态 |
|---|------|------|------|
| 1 | 双层：rules.md + episodes.md + reference/ | 行业共识 + 项目验证 | ✅ |
| 2 | 双通道落库：hook 自动 + @reflect 人工 | 自动防遗漏，人工补复杂洞察 | ✅ |
| 3 | 自动落库只处理简单模式（别用X/换成Y） | shell regex 能力有限，宁可漏掉不写垃圾 | ✅ |
| 4 | episodes.md append-only，hook 不做删除 | 避免 sed -i 跨平台问题 | ✅ |
| 5 | 去重用 grep -c 实时计数，不原地更新 ×N | shell 原地修改不可靠 | ✅ |
| 6 | 质量报告写文件，context 只放一行指针 | 避免 Stop hook 频繁输出消耗 context | ✅ |
| 7 | 容量淘汰由人/agent 执行，hook 只报告 | hook 只 append 不 delete，简单可靠 | ✅ |
| 8 | 落库 pipeline 拆独立脚本 | context-enrichment.sh 不宜过重 | ✅ |
| 9 | promote_candidate 不存储，实时计算 | append-only 原则，不原地改 status | ✅ |
| 10 | keywords 只提取英文技术术语 | grep -iw 对中文 word boundary 无效 | ✅ |
| 11 | auto-capture 用 exit code 区分结果 | 避免自动捕获后仍提醒 self-reflect | ✅ |

### Limitações Conhecidas
- 并发写入：多 agent 同时 append episodes.md 理论上有竞争，当前规模（≤30 条，低频）可接受

---

## Passos

### Tarefa 0: 备份

```bash
cp knowledge/lessons-learned.md knowledge/lessons-learned.md.bak
git status --short knowledge/
```

### Tarefa 1: 创建 rules.md + episodes.md

**Arquivos:** Create `knowledge/rules.md`, `knowledge/episodes.md`; Delete `knowledge/lessons-learned.md`

**Step 1: 提炼 rules.md**

从 lessons-learned.md 的 Mistakes/Wins/Rules Extracted 中提炼，格式：

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

每条规则要求：
- 有明确 DO/DON'T 动作
- ≤2 行
- 有触发场景
- 不含叙事（叙事在 episodes.md）
- 已有 hook 的标注 `[hook: xxx]`

**Step 2: 创建 episodes.md**

从 lessons-learned.md 重构，合并重复，格式改为 shell-friendly 行格式。

**格式约束：所有条目的 SUMMARY 字段不得包含 `|` 字符（用 `/` 替代），确保 `cut -d'|'` 字段解析正确。**

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

**Step 3: 删除旧文件**

```bash
rm knowledge/lessons-learned.md
```

**Step 4: 验证**

```bash
wc -c knowledge/rules.md                                          # ≤2048
grep -c '^[0-9]' knowledge/rules.md                                # ≤30
grep -c '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} |' knowledge/episodes.md  # ≤30
test ! -f knowledge/lessons-learned.md && echo "DELETED"
```

### Tarefa 2: 自动落库 pipeline（hook）

**Arquivos:** Create `hooks/feedback/auto-capture.sh`; Modify `hooks/feedback/context-enrichment.sh`

**Step 1: 创建 auto-capture.sh**

独立脚本，由 context-enrichment.sh 在检测到纠正后调用。

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

**Step 2: 修改 context-enrichment.sh**

纠正检测后调用 auto-capture.sh：

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

rules.md 注入改为动态读取：

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

**Step 3: 验证**

```bash
# 模拟纠正消息测试 pipeline
echo '别用sed处理JSON，用jq' | bash hooks/feedback/auto-capture.sh "别用sed处理JSON，用jq"
cat knowledge/episodes.md | tail -1
```

### Tarefa 3: 质量报告生成

**Arquivos:** Create `hooks/feedback/kb-health-report.sh`; Modify Stop hook

**Step 1: 创建 kb-health-report.sh**

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

**Step 2: 在 Stop hook 中调用**

```bash
bash "$(dirname "$0")/../feedback/kb-health-report.sh"
```

**Step 3: 验证**

```bash
touch "/tmp/kb-changed-$(pwd | shasum | cut -c1-8).flag"
bash hooks/feedback/kb-health-report.sh
cat knowledge/.health-report.md
```

### Tarefa 4: @reflect 命令（人工落库通道）

**Arquivos:** Create `.kiro/prompts/reflect.md` (Kiro) 或 `.claude/commands/reflect.md` (CC)

**Step 1: 创建 reflect prompt**

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

**Step 2: 验证**

```bash
# Kiro
test -f .kiro/prompts/reflect.md && echo "EXISTS"
# CC
test -f .claude/commands/reflect.md && echo "EXISTS"
```

### Tarefa 5: self-reflect skill 简化

**Arquivos:** Modify `skills/self-reflect/SKILL.md`

收窄职责为两个场景：

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

更新 Sync Targets 表：

```markdown
## Sync Targets

| Scenario | Target |
|----------|--------|
| Promotion (≥3 same pattern) | knowledge/rules.md |
| Complex insight | knowledge/episodes.md |
| Code-enforceable rule | .kiro/rules/enforcement.md |
```

### Tarefa 6: 更新 INDEX.md、AGENTS.md 和全局引用

**Arquivos:** Modify `knowledge/INDEX.md`, `AGENTS.md`, grep 全项目清理

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

Knowledge Retrieval 段更新：
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

**Step 3: 全局引用清理**

```bash
grep -r 'lessons-learned' . --include='*.md' --include='*.sh' | grep -v '.git' | grep -v '.bak' | grep -v 'archive/'
# 将所有引用更新为 rules.md 或 episodes.md
```

**Step 4: 验证**

```bash
grep -r 'lessons-learned' . --include='*.md' --include='*.sh' | grep -v '.git' | grep -v '.bak' | grep -v 'archive/' || echo "CLEAN"
```

---

## Review

### Strengths
- **双通道互补**: hook 自动防遗漏 + @reflect 人工补复杂洞察
- **hook 驱动**: 落库、召回、报告全部 hook 保证，不依赖 agent 自主行为
- **事前质量控制**: 4-Gate pipeline 过滤低价值、去重、容量控制
- **事后低门槛治理**: 质量报告写文件，一行指针进 context，人看报告就知道该做什么
- **shell 操作简单可靠**: append-only，不原地修改，不跨平台 sed -i
- **context 成本可控**: rules 注入仅首次，报告仅一行指针，晋升提醒仅一行
- **exit code 区分**: auto-capture 成功 vs 被过滤，避免冗余 self-reflect 提醒
- **实时计算晋升**: 不存储 promote_candidate 状态，和 append-only 原则一致

### Risks & Mitigations
- **自动落库写入垃圾**: Gate 1 严格过滤（问句/无动作 → 丢弃），有动作的不受长度限制，SUMMARY 截断到 80 字符
- **关键词 grep 误匹配**: 仅英文技术术语 ≥4 字符 + grep -iw（word boundary）
- **episodes.md 格式损坏**: 用户消息中 `|` 替换为 `/`，行格式而非表格
- **容量溢出**: 满 30 条时拒绝写入 + 报告提醒，不自动删除
- **@reflect 人忘记用**: 可接受——复杂洞察本身低频，自动通道已覆盖高频场景
- **并发写入**: 多 agent 同时 append 理论有竞争，当前规模可接受

### Verdict: **APPROVED**

## Checklist

- [ ] knowledge/lessons-learned.md.bak 备份已创建
- [ ] knowledge/rules.md 已创建，≤2KB，≤30 条，每条有 DO/DON'T + 触发场景
- [ ] knowledge/episodes.md 已创建，行格式（非表格），重复已合并，有 status 列
- [ ] hooks/feedback/auto-capture.sh 已创建，4-Gate pipeline，exit 0/1 区分
- [ ] auto-capture Gate 1: 问句丢弃、无动作丢弃（有动作不受长度限制，SUMMARY 截断 80 字符）
- [ ] auto-capture 预检查: episodes.md 不存在时 exit 1
- [ ] auto-capture Gate 2: 仅英文技术术语 ≥4 字符，排除常见词
- [ ] auto-capture Gate 3: grep -iwE 去重，实时 grep -c 计数晋升提醒
- [ ] auto-capture Gate 4: 容量 ≥30 拒绝写入
- [ ] context-enrichment.sh 根据 auto-capture exit code 决定是否提醒 self-reflect
- [ ] context-enrichment.sh 动态读 rules.md，有 fallback 硬编码
- [ ] context-enrichment.sh 会话开始实时计算晋升候选（关键词频次 ≥3）
- [ ] context-enrichment.sh 会话开始检查 .health-report.md 有无 issues
- [ ] hooks/feedback/kb-health-report.sh 已创建，三条件触发（变更+有问题+首次）
- [ ] kb-health-report 晋升候选通过实时关键词频次计算，不依赖存储状态
- [ ] kb-health-report 日期匹配用 `[0-9]{4}-[0-9]{2}-[0-9]{2} |` 而非 `^20`
- [ ] Stop hook 调用 kb-health-report.sh
- [ ] knowledge/.health-report.md 自动生成，context 只一行指针
- [ ] @reflect prompt 已创建（.kiro/prompts/ 和/或 .claude/commands/）
- [ ] self-reflect SKILL.md 已简化（只负责晋升执行 + 复杂洞察辅助）
- [ ] knowledge/INDEX.md 路由表已更新
- [ ] AGENTS.md 已更新（双通道描述）
- [ ] grep -r 'lessons-learned' 全项目无残留引用（.bak 和 archive/ 除外）
- [ ] 模拟测试：简单纠正 → auto-capture exit 0 → episodes.md 有新条目
- [ ] 模拟测试：复杂纠正 → auto-capture exit 1 → 提醒 self-reflect
- [ ] 模拟测试：重复纠正 → 去重跳过 → ≥3 次输出 🔥 晋升提醒
- [ ] 模拟测试：kb-health-report 生成正确，晋升候选通过关键词频次计算
