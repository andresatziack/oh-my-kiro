# v3 Cleanup & Hardening

**Objetivo:** 清理 v2→v3 迁移残留，增强纠正检测覆盖率，提升 verify-completion 可见性，消除 self-reflect 设计矛盾。
**Arquitetura:** 纯文件删除/修改，不新增模块。涉及 skills/、hooks/、knowledge/ 三个目录。
**Escopo:** 4 项变更，无新依赖。

## Decisões

| # | 决策 | 原因 | 状态 |
|---|------|------|------|
| 1 | 删除 PRODUCT.md 机制而非填充 | 框架本身不需要产品地图，空壳浪费 context | ✅ 采纳 |
| 2 | verify-completion 输出加强 + 前移到 require-workflow gate | Stop hook 在 Kiro 不能阻断，前移到 PreToolUse 才能硬拦截 | ✅ 采纳 |
| 3 | 纠正检测只扩充正则，不引入 LLM | keep simple，确定性优先，不够用以后再增强 | ✅ 采纳 |
| 4 | 删除 self-reflect queue 机制 | v2 遗留，与 v3 "immediate write" 原则矛盾 | ✅ 采纳 |
| 5 | 度量/可观测性不做 | 优先级不高，以后再说 | ❌ 推迟 |

## Passos

### Tarefa 1: 删除 PRODUCT.md 机制

**Arquivos:**
- Delete: `knowledge/product/PRODUCT.md`
- Delete: `knowledge/product/INDEX.md`
- Delete: `knowledge/product/` (目录)
- Modify: `skills/brainstorming/SKILL.md` — 移除 "read PRODUCT.md" 引用
- Modify: `skills/planning/SKILL.md` — 移除 "read PRODUCT.md" 引用和 Phase 3 更新 PRODUCT.md
- Modify: `knowledge/INDEX.md` — 移除 product 相关路由条目

**Step 1: 删除文件和目录**
```bash
rm -rf knowledge/product/
```

**Step 2: 清理 brainstorming skill**
移除 `If knowledge/product/PRODUCT.md exists and is non-empty, read it first` 相关行。

**Step 3: 清理 planning skill**
移除 `Before writing: Read knowledge/product/PRODUCT.md` 和 Phase 3 中 `Update knowledge/product/PRODUCT.md if features changed`。

**Step 4: 清理 knowledge/INDEX.md**
移除 `Product features & constraints` 路由行和 Quick Links 中的 Product Map 链接。

**Step 5: 验证（全面搜索）**
```bash
grep -r "PRODUCT.md\|product/INDEX\|knowledge/product" skills/ knowledge/ hooks/ commands/ CLAUDE.md AGENTS.md .claude/rules/ 2>/dev/null | grep -v '.git' || echo "CLEAN"
```

### Tarefa 2: verify-completion 增强 + 前移检查

**Arquivos:**
- Modify: `hooks/feedback/verify-completion.sh` — 输出格式加强
- Modify: `hooks/gate/require-workflow.sh` — 增加 checklist 未完成检查

**Step 1: 加强 verify-completion.sh 输出格式**
将 `⚠️ INCOMPLETE` 改为更醒目的格式：
```
🚫 ═══════════════════════════════════════
🚫 INCOMPLETE: N/M checklist items remaining
🚫 ═══════════════════════════════════════
```

**Step 2: require-workflow.sh 增加 checklist 前移检查**
在 verdict 检查通过后（exit 0 之前），增加 advisory 检查：

```bash
# 8. Advisory: remind about unchecked items
UNCHECKED=$(grep -c '^\- \[ \]' "$PLAN_FILE" 2>/dev/null || true)
CHECKED=$(grep -c '^\- \[x\]' "$PLAN_FILE" 2>/dev/null || true)
if [ "${UNCHECKED:-0}" -gt 0 ]; then
  echo "📋 Progress: $CHECKED/$((CHECKED + UNCHECKED)) checklist items done in $PLAN_FILE" >&2
fi
```

不阻断（exit 0），因为正在写代码说明正在完成 checklist 项。但每次写文件都提醒进度。

**Step 3: 验证**
```bash
bash hooks/feedback/verify-completion.sh < /dev/null; echo "exit: $?"
```

### Tarefa 3: 扩充纠正检测正则

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh` — 扩充正则模式

**Step 1: 增加隐式否定模式**
在现有 3 个 `elif` 分支后增加第 4 个分支，覆盖：
- 中文隐式否定：`不是我(想要|要的|期望|需要)的`、`换个(思路|方式|方法|方案)`、`不是这样`、`这样不行`、`重新来`、`不是我要的`、`不够好`、`差太远`、`完全不对`、`跑偏了`、`方向错了`
- 英文隐式否定：`not what I (want|need|expect|asked)`、`try (again|different|another)`、`wrong approach`、`start over`、`that's not it`、`off track`、`missed the point`

**Step 2: 验证（含误触发测试）**
```bash
# 应触发
echo '{"prompt":"这不是我想要的效果"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"换个思路吧"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"not what I wanted"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"try a different approach"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"完全不对"}' | bash hooks/feedback/context-enrichment.sh
# 不应触发
echo '{"prompt":"今天天气不错"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"帮我写个函数"}' | bash hooks/feedback/context-enrichment.sh
echo '{"prompt":"这个方案不错，继续"}' | bash hooks/feedback/context-enrichment.sh
```

### Tarefa 4: 删除 self-reflect queue 机制

**Arquivos:**
- Delete: `skills/self-reflect/reflect_utils.py`
- Delete: `skills/self-reflect/commands/reflect.md`
- Delete: `skills/self-reflect/commands/view-queue.md`
- Delete: `skills/self-reflect/commands/skip-reflect.md`
- Delete: `skills/self-reflect/commands/` (目录)
- Modify: `skills/self-reflect/SKILL.md` — 移除 Commands 表格中 queue 相关命令

**Step 1: 删除文件**
```bash
rm -f skills/self-reflect/reflect_utils.py
rm -rf skills/self-reflect/commands/
```

**Step 2: 清理 SKILL.md**
移除 Commands 段落中的 `/reflect`、`/view-queue`、`/skip-reflect` 行，以及 "Review & Sync" 示例。

**Step 3: 验证**
```bash
ls skills/self-reflect/
# 应该只剩 SKILL.md
grep -c 'queue\|/reflect\|/view-queue\|/skip-reflect' skills/self-reflect/SKILL.md
# 应该输出 0
```

## Review

### Round 1 - REQUEST CHANGES (resolvido)

**Pontos fortes:**
- Escopo claro com 4 mudanças focadas, sem expansão indevida
- Checklist concreto com 13 critérios de aceitação testáveis
- Cada tarefa tem comandos de verificação para feedback imediato
- Aborda dívida técnica real (PRODUCT.md vazio, mecanismo de queue do v2)
- Progressão lógica: deletar não usado -> aprimorar existente -> expandir detecção -> remover contraditório

**Pontos fracos:**
- ~~Tarefa 2 Passo 2 é vago: "输出警告（不阻断）" - qual o formato exato do aviso?~~ -> Corrigido: bash code exato adicionado
- Sem plano de rollback se arquivos modificados -> Não necessário: git rastreia todas as mudanças
- ~~Padrões regex da Tarefa 3 podem gerar falsos positivos~~ -> Corrigido: adicionados 3 casos negativos + 3 itens de checklist
- ~~Falta análise de impacto em fluxos existentes que poderiam depender de PRODUCT.md~~ -> Corrigido: escopo do grep ampliado

**Faltando:**
- ~~Estratégia de backup pré-execução para arquivos modificados~~ -> git é o backup
- ~~Plano de testes para casos de borda no regex de context-enrichment.sh~~ -> Corrigido: 5 casos positivos + 3 negativos
- ~~Atualizações de documentação~~ -> atualização de knowledge/INDEX.md já está na Tarefa 1
- ~~Consideração de conflitos de execução concorrente de planos~~ -> N/A, framework single-user

**Correções necessárias (todas resolvidas):**
1. ~~Especificar formato e lógica de aviso exatos para Tarefa 2 Passo 2~~ -> Pronto
2. ~~Adicionar passo de backup antes de modificações de arquivo~~ -> git é suficiente
3. ~~Adicionar checagem grep abrangente para todas as referências antes de deletar~~ -> Pronto
4. ~~Definir estratégia de teste de regex para prevenir falsos positivos~~ -> Pronto

### Round 2 - APPROVE

**Avaliação das correções do Round 1:**
✅ Todas as 4 correções obrigatórias foram tratadas:
1. Tarefa 2 Passo 2 agora tem bash code exato para exibição de progresso do checklist
2. Estratégia de backup: git é o backup (rejeitada como desnecessária)  
3. Checagem grep ampliada para cobrir diretórios hooks/commands/rules
4. Adicionados 5 casos positivos + 3 negativos de regex e 3 itens adicionais de checklist para falsos positivos

**Detalhe de implementação:**
✅ Suficiente - cada tarefa tem comandos bash concretos, paths de arquivo e passos de verificação
✅ Bash code da Tarefa 2 Passo 2 está pronto para produção
✅ Padrões regex da Tarefa 3 são abrangentes com testes adequados
✅ Todos os 16 itens do checklist são testáveis e específicos

**Lacunas/riscos remanescentes:**
⚠️ Menor: regex da Tarefa 3 ainda pode ter casos de borda, mas a estratégia de teste mitiga isso
⚠️ Menor: sem procedimento de rollback além do git, mas as mudanças são operações de arquivo de baixo risco
✅ Nenhum problema bloqueante identificado

**Veredito: APPROVE**
- Todo o feedback do Round 1 incorporado
- Detalhe de implementação suficiente para execução
- Nível de risco aceitável para tarefas de limpeza
- Estratégia de verificação clara para cada mudança

## Checklist

- [x] knowledge/product/ 目录已删除
- [x] brainstorming skill 不再引用 PRODUCT.md
- [x] planning skill 不再引用 PRODUCT.md
- [x] knowledge/INDEX.md 不再引用 product
- [x] grep -r "PRODUCT.md" 在 skills/knowledge/hooks/commands/rules 下无结果
- [x] verify-completion.sh 输出格式更醒目
- [x] require-workflow.sh 包含 checklist 未完成检查
- [x] context-enrichment.sh 能匹配 "这不是我想要的效果"
- [x] context-enrichment.sh 能匹配 "换个思路"
- [x] context-enrichment.sh 能匹配 "not what I wanted"
- [x] context-enrichment.sh 不误触发 "今天天气不错"
- [x] context-enrichment.sh 不误触发 "帮我写个函数"
- [x] context-enrichment.sh 不误触发 "这个方案不错，继续"
- [x] reflect_utils.py 已删除
- [x] self-reflect/commands/ 目录已删除
- [x] self-reflect SKILL.md 不再包含 queue/reflect/view-queue 相关内容
