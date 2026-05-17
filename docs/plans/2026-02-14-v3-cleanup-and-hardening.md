# v3 Cleanup & Hardening

**Objetivo:** Limpar residuos da migracao v2->v3, ampliar a cobertura da deteccao de correction, melhorar a visibilidade de verify-completion e eliminar contradicoes de design em self-reflect.
**Arquitetura:** Apenas remover/modificar arquivos, sem novos modulos. Envolve tres diretorios: skills/, hooks/, knowledge/.
**Escopo:** 4 mudancas, sem novas dependencias.

## Decisões

| # | Decisao | Motivo | Status |
|---|------|------|------|
| 1 | Remover o mecanismo PRODUCT.md em vez de preencher | O proprio framework nao precisa de mapa de produto; uma casca vazia so consome context | ✅ Adotado |
| 2 | Reforcar a saida de verify-completion + antecipar para o gate require-workflow | Stop hook nao bloqueia no Kiro; antecipar para PreToolUse permite bloqueio forte | ✅ Adotado |
| 3 | Apenas ampliar o regex da deteccao de correction; sem usar LLM | Manter simples, priorizar determinismo; melhoramos depois se nao bastar | ✅ Adotado |
| 4 | Remover o mecanismo de queue da self-reflect | Heranca do v2 que contradiz o principio "immediate write" do v3 | ✅ Adotado |
| 5 | Metricas/observabilidade nao entram | Prioridade baixa, fica para depois | ❌ Adiado |

## Passos

### Tarefa 1: remover o mecanismo PRODUCT.md

**Arquivos:**
- Delete: `knowledge/product/PRODUCT.md`
- Delete: `knowledge/product/INDEX.md`
- Delete: `knowledge/product/` (diretorio)
- Modify: `skills/brainstorming/SKILL.md` - remover referencias a "read PRODUCT.md"
- Modify: `skills/planning/SKILL.md` - remover referencias a "read PRODUCT.md" e o passo da Phase 3 que atualizava PRODUCT.md
- Modify: `knowledge/INDEX.md` - remover entradas de roteamento relacionadas a product

**Step 1: apagar arquivos e diretorios**
```bash
rm -rf knowledge/product/
```

**Step 2: limpar a brainstorming skill**
Remover linhas como `If knowledge/product/PRODUCT.md exists and is non-empty, read it first`.

**Step 3: limpar a planning skill**
Remover `Before writing: Read knowledge/product/PRODUCT.md` e o `Update knowledge/product/PRODUCT.md if features changed` da Phase 3.

**Step 4: limpar knowledge/INDEX.md**
Remover a linha de routing `Product features & constraints` e o link Product Map em Quick Links.

**Step 5: validacao (busca abrangente)**
```bash
grep -r "PRODUCT.md\|product/INDEX\|knowledge/product" skills/ knowledge/ hooks/ commands/ CLAUDE.md AGENTS.md .claude/rules/ 2>/dev/null | grep -v '.git' || echo "CLEAN"
```

### Tarefa 2: reforcar verify-completion + antecipar a checagem

**Arquivos:**
- Modify: `hooks/feedback/verify-completion.sh` - reforcar formato da saida
- Modify: `hooks/gate/require-workflow.sh` - adicionar checagem de itens nao concluidos no checklist

**Step 1: deixar a saida de verify-completion.sh mais visivel**
Trocar `⚠️ INCOMPLETE` por:
```
🚫 ═══════════════════════════════════════
🚫 INCOMPLETE: N/M checklist items remaining
🚫 ═══════════════════════════════════════
```

**Step 2: require-workflow.sh com checagem de checklist antecipada**
Apos a checagem de verdict passar (antes do exit 0), incluir um aviso advisory:

```bash
# 8. Advisory: remind about unchecked items
UNCHECKED=$(grep -c '^\- \[ \]' "$PLAN_FILE" 2>/dev/null || true)
CHECKED=$(grep -c '^\- \[x\]' "$PLAN_FILE" 2>/dev/null || true)
if [ "${UNCHECKED:-0}" -gt 0 ]; then
  echo "📋 Progress: $CHECKED/$((CHECKED + UNCHECKED)) checklist items done in $PLAN_FILE" >&2
fi
```

Sem bloquear (exit 0): se o agent esta escrevendo codigo, e por que esta cumprindo a checklist; mas a cada escrita o progresso e mostrado.

**Step 3: validacao**
```bash
bash hooks/feedback/verify-completion.sh < /dev/null; echo "exit: $?"
```

### Tarefa 3: ampliar regex da deteccao de correction

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh` - ampliar os patterns

**Step 1: incluir patterns de negacao implicita**
Apos os 3 ramos `elif` existentes, adicionar um quarto cobrindo:
- Negacao implicita em chines: `不是我(想要|要的|期望|需要)的`, `换个(思路|方式|方法|方案)`, `不是这样`, `这样不行`, `重新来`, `不是我要的`, `不够好`, `差太远`, `完全不对`, `跑偏了`, `方向错了`
- Negacao implicita em ingles: `not what I (want|need|expect|asked)`, `try (again|different|another)`, `wrong approach`, `start over`, `that's not it`, `off track`, `missed the point`

**Step 2: validacao (incluindo testes de falso positivo)**
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

### Tarefa 4: remover o mecanismo de queue da self-reflect

**Arquivos:**
- Delete: `skills/self-reflect/reflect_utils.py`
- Delete: `skills/self-reflect/commands/reflect.md`
- Delete: `skills/self-reflect/commands/view-queue.md`
- Delete: `skills/self-reflect/commands/skip-reflect.md`
- Delete: `skills/self-reflect/commands/` (diretorio)
- Modify: `skills/self-reflect/SKILL.md` - remover da tabela de Commands as entradas relacionadas a queue

**Step 1: apagar arquivos**
```bash
rm -f skills/self-reflect/reflect_utils.py
rm -rf skills/self-reflect/commands/
```

**Step 2: limpar SKILL.md**
Remover na secao Commands as linhas de `/reflect`, `/view-queue`, `/skip-reflect`, alem do exemplo "Review & Sync".

**Step 3: validacao**
```bash
ls skills/self-reflect/
# So deve restar SKILL.md
grep -c 'queue\|/reflect\|/view-queue\|/skip-reflect' skills/self-reflect/SKILL.md
# Deve imprimir 0
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
- ~~Tarefa 2 Passo 2 é vago: "exibir warning (sem bloquear)" - qual o formato exato do aviso?~~ -> Corrigido: bash code exato adicionado
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

- [x] diretorio knowledge/product/ removido
- [x] brainstorming skill nao referencia mais PRODUCT.md
- [x] planning skill nao referencia mais PRODUCT.md
- [x] knowledge/INDEX.md nao referencia mais product
- [x] grep -r "PRODUCT.md" sob skills/knowledge/hooks/commands/rules sem resultado
- [x] saida de verify-completion.sh esta mais visivel
- [x] require-workflow.sh inclui a checagem de itens nao concluidos no checklist
- [x] context-enrichment.sh casa "这不是我想要的效果"
- [x] context-enrichment.sh casa "换个思路"
- [x] context-enrichment.sh casa "not what I wanted"
- [x] context-enrichment.sh nao dispara para "今天天气不错"
- [x] context-enrichment.sh nao dispara para "帮我写个函数"
- [x] context-enrichment.sh nao dispara para "这个方案不错，继续"
- [x] reflect_utils.py removido
- [x] diretorio self-reflect/commands/ removido
- [x] SKILL.md de self-reflect nao contem mais conteudo relacionado a queue/reflect/view-queue
