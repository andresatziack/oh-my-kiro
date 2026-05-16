# 精简 Hook 输出 - 为 Auto-Compaction 留出 32K 空间

**Objetivo:** 减少 hook 输出的 token 占用，确保 context 在 auto-compact 触发时仍有 ≥32K 空间供 compaction API 调用。

**Causa Raiz:** Kiro auto-compact 触发时需要 ~32K max_tokens。如果 input 已超 168K（200K-32K），compact 请求本身会被 API 拒绝（#1531）。Hook 输出是最大的可控 token 消耗源。

## 精简方案

### 1. context-enrichment.sh（最大优化点）

**当前：** 每次用户输入注入 4 行 lessons（~200 tokens × 20 轮 = ~4000 tokens）
**改为：** 用 /tmp flag 文件控制，只在 session 首次注入
**省：** ~3800 tokens / 20 轮

**影响：** lessons 只在 session 开头出现一次。如果 agent 在后期违反规则（如用 sed 改 JSON），没有重复提醒。但 block-sed-json.sh 是硬拦截（exit 2），所以 lessons 提醒本身是冗余的安全网。影响极小。

### 2. inject-plan-context.sh（第二大优化点）

**当前：** 每次 write 注入整个 checklist section（~300 tokens × 60 次 write = ~18000 tokens）
**改为：** 用 /tmp 计数器，每 5 次 write 注入完整 checklist，其他时候只输出 1 行"📋 N items remaining in plan"
**省：** ~14400 tokens / 20 轮（60 次 write 中 12 次完整注入 + 48 次 1 行）

**影响：** agent 每 5 次 write 仍能看到完整 checklist，防止长 session 中目标被挤出 attention。比完全移除安全得多。

### 3. verify-completion.sh（不改）

保留完整输出（数量 + 具体未完成项）。只在 stop 时触发一次，token 开销小，但 agent 需要看到具体哪些没完成。

### 4. remind-update-progress.sh（已经很精简）

**当前：** 1 行提醒，且 *.md/*.json 已跳过
**改为：** 不变
**影响：** 无

### 5. auto-test.sh（小优化）

**当前：** 失败时输出 `tail -20`（最多 20 行）
**改为：** 失败时输出 `tail -10`（最多 10 行）
**省：** ~500 tokens（条件触发）

**影响：** 测试失败信息少了 10 行。通常前 10 行已包含关键错误。影响极小。

## 预估效果

| Hook | 当前 (20轮) | 精简后 (20轮) | 节省 |
|------|------------|-------------|------|
| context-enrichment lessons | ~4000 tokens | ~200 tokens | 3800 |
| inject-plan-context | ~18000 tokens | ~3600 tokens | 14400 |
| verify-completion | ~1000 tokens | ~1000 tokens | 0 |
| auto-test | ~2000 tokens | ~1000 tokens | 1000 |
| **合计** | **~25000** | **~5800** | **~19200** |

节省 ~19K tokens。加上原有余量，给 compaction 留出更多空间。

## Checklist
- [x] context-enrichment.sh: lessons 用 /tmp flag 控制只注入一次
- [x] inject-plan-context.sh: 用 /tmp 计数器，每 5 次 write 注入完整 checklist，其他时候只输出 1 行数量
- [x] auto-test.sh: tail -20 改为 tail -10
- [x] 所有修改后 bash -n 验证无语法错误

## Review

**VERDITO: REQUEST CHANGES**

**Problemas críticos:**
1. ✅ **Checklist existe** com critérios de aceitação concretos `- [ ]`
2. ❌ **Erro de matemática de tokens**: alega 29K de espaço total, mas precisa de 32K para compaction
   - Atual: ~7K de margem + 22K economizados = 29K < 32K necessários
   - **Lacuna: 3K tokens ainda faltam**
3. ❌ **Avaliação de risco incompleta**: faltam análises sobre impacto no debugging quando os hooks fornecem menos contexto

**Preocupações específicas:**
- **Mudança em inject-plan-context.sh é DE ALTO RISCO**: remover a visibilidade do checklist durante sessões longas de coding pode fazer agentes perderem o rastro dos requisitos. A premissa "ralph-loop lê o plan no início" cai por terra se a sessão tiver >50 operações empurrando o checklist para fora da janela de context.
- **Mudança em verify-completion.sh reduz a eficiência de debugging**: quando builds falham, agentes precisam ver QUAIS itens estão incompletos, não só a contagem.

**Mudanças necessárias:**
1. Corrigir a matemática de tokens: encontrar 3K adicionais de economia ou reduzir o requisito de compaction
2. Adicionar mecanismo de fallback para inject-plan-context.sh (por exemplo, reinjetar o checklist a cada 10 operações)
3. Quantificar o impacto no debugging: quanto mais lenta será a resolução de issues sem a saída detalhada dos hooks?

**Sugestões:**
- Considerar redução progressiva: começar apenas pelo context-enrichment.sh (3.8K de economia), medir o impacto antes de mexer na injeção de plan
- Adicionar métricas para acompanhar com que frequência agentes releem planos após mudanças nos hooks
