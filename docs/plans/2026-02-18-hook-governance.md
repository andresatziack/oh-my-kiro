# Hook Governance - auditoria, otimizacao, fixacao

**Objetivo:** Auditar todo o sistema de hooks, corrigir inconsistencias e redundancias, produzir o Hook Architecture Design Doc (com decisoes de extensibilidade) e fixar essas decisoes via codigo para que iteracoes futuras nao quebrem o desenho, garantindo tambem um fluxo claro para integrar hooks novos.

**Não-Objetivos:**
- Sem novas funcionalidades de hook (ex.: Stop hook com LLM eval, auto-approve, etc.)
- Sem refatorar a estrategia de merge de pre-write.sh (a uniao atual e proposital, reduzindo o numero de invocacoes)
- Sem mexer na taxonomia security/gate/feedback

**Arquitetura:** Tres camadas de governanca: (1) enforcement.md vira o Hook Architecture Doc completo, com principios de classificacao, regras de nomeclatura e fronteiras de responsabilidade; (2) generate_configs.py adiciona validacao de consistencia, garantindo que o config gerado bate com o architecture doc; (3) o gate pre-write protege a pasta hooks/, exigindo que mudancas nela ocorram em paralelo a atualizacao do architecture doc.

**Tech Stack:** Bash (hooks), Python (generator/validator), Markdown (architecture doc)

## Audit Findings

### F1: drift do registro - enforcement.md sem 2 hooks
`enforce-ralph-loop.sh` e `require-regression.sh` estao em generate_configs.py e nos JSON dos agents do Kiro, mas faltam em enforcement.md. enforcement.md, como "fonte unica da verdade", esta incompleto.

### F2: drift do registro - settings.json sem 2 hooks
`enforce-ralph-loop.sh` e `require-regression.sh` estao nos JSON do Kiro, mas faltam em `.claude/settings.json`. Em CC, esses dois gates nunca disparam.

### F3: llm-eval.sh e codigo morto
`_lib/llm-eval.sh` existe mas nenhum hook faz source dele. O design v2 previa um Stop hook com LLM eval, mas nunca foi conectado. 50 linhas de codigo morto.

### F4: numeracao confusa de Phase em pre-write.sh
A ordem das Phases e 0 -> 1 -> 2 -> 3 -> 1.5a0 -> 1.5a -> 1.5b. A numeracao nao reflete a ordem de execucao (a familia Phase 1.5 esta declarada apos Phase 2/3 mas roda antes da Phase 2). Nao afeta funcionalidade, mas reduz legibilidade.

### F5: auto-capture.sh e kb-health-report.sh sao "shadow hooks"
Esses dois scripts nao estao registrados em settings.json nem nos JSON dos agents; sao chamados por outros hooks (correction-detect -> auto-capture, verify-completion -> kb-health-report). enforcement.md nao documenta essa relacao.

### F6: session-init.sh com responsabilidades demais
73 linhas, com 5 responsabilidades: episode cleanup, rules injection, promotion reminder, delegation reminder, KB health report. Entre elas, o delegation reminder e uma linha echo hardcoded, impressa toda session, com valor questionavel.

### F7: block-outside-workspace.sh registrado duas vezes em cada agent
Em default.json, executor.json, pilot.json, researcher.json e reviewer.json, block-outside-workspace.sh aparece duas vezes (uma com matcher=execute_bash, outra com matcher=fs_write). Esta correto (eventos diferentes), mas enforcement.md so registra uma entrada.

### F8: fronteiras das tres categorias estao borradas
- `gate/` = bloqueia (exit 2), porem `inject_plan_context` em `pre-write.sh` e advisory (nao bloqueia)
- `feedback/` = nao bloqueia, porem `run_test` em `post-write.sh` retorna exit 1 (o comportamento de exit 1 em PostToolUse nao esta documentado)
- O principio de classificacao nao esta documentado

### F9: tabela Determinism Layers incompleta
A tabela Determinism Layers em enforcement.md so tem 3 camadas (Commands/Gate/Feedback); falta a L0 (security hooks, tambem sao 100% hard block). security e gate, ambos exit 2 de bloqueio, estao em camadas diferentes.

### F10: cobertura de testes desigual
Com testes: block-dangerous, block-sed-json, instruction-guard (brainstorm-gate + write-protection), block-recovery, context-enrichment split, kiro-compat
Sem testes: block-secrets, block-outside-workspace, enforce-ralph-loop, require-regression, session-init, correction-detect, auto-capture, kb-health-report, verify-completion, post-write, post-bash

## Tarefas

### Tarefa 1: corrigir drift do registro + remover codigo morto

**Arquivos:**
- Modify: `hooks/_lib/llm-eval.sh` -> mover para `.trash/`
- Modify: `.kiro/rules/enforcement.md`

**Step 1: remover o codigo morto llm-eval.sh**
```bash
mv hooks/_lib/llm-eval.sh .trash/llm-eval.sh
```

**Step 2: reescrever enforcement.md como registro completo**
Atualizar enforcement.md, contemplando todos os 15 hooks (incluindo os 2 shadow hooks) e indicando relacoes de chamada e estado de registro.

**Verificação:**
```bash
# 验证 llm-eval.sh 已移除
test ! -f hooks/_lib/llm-eval.sh
```

### Tarefa 2: corrigir drift de settings.json

**Arquivos:**
- Modify: `scripts/generate_configs.py`

**Step 1: confirmar se generate_configs.py ja inclui as versoes CC de enforce-ralph-loop e require-regression**
Inspecionar a logica de geracao do CC settings.json em generate_configs.py e completar os hooks faltantes.

**Step 2: regenerar configs**
```bash
python3 scripts/generate_configs.py
```

**Verificação:**
```bash
# 验证 settings.json 包含 enforce-ralph-loop
jq -r '.. | .command? // empty' .claude/settings.json | grep -q 'enforce-ralph-loop'
```

### Tarefa 3: corrigir a numeracao de Phase em pre-write.sh

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh`

**Step 1: renumerar as Phases**
Renumerar conforme a ordem real de execucao:
- Phase 0: Instruction File Write Protection (inalterado)
- Phase 1: Workflow Gate (inalterado)
- Phase 2: Brainstorming Gate (era 1.5a0)
- Phase 3: Plan Structure Rubric (era 1.5a)
- Phase 4: Checklist Check-off Gate (era 1.5b)
- Phase 5: Injection & Secret Scan (era 2)
- Phase 6: Plan Context Injection (era 3, advisory)

**Verificação:**
```bash
# 验证 Phase 编号连续且递增
grep -E '^# Phase [0-9]' hooks/gate/pre-write.sh | awk '{print $3}' | sort -n -c 2>&1; echo "exit: $?"
```

### Tarefa 4: limpar saidas de baixo valor em session-init.sh

**Arquivos:**
- Modify: `hooks/feedback/session-init.sh`

**Step 1: remover o delegation reminder hardcoded**
Apagar `echo "⚡ Delegation: >3 independent tasks → use subagent per task. Never delegate code/grep/web_search tasks."`. Esse echo e ruido em toda session, e as regras de subagent ja vivem em `.claude/rules/subagent.md`.

**Verificação:**
```bash
# 验证 delegation reminder 已移除
! grep -q 'Delegation:' hooks/feedback/session-init.sh
```

### Tarefa 5: produzir o Hook Architecture Design Doc

**Arquivos:**
- Create: `docs/designs/2026-02-18-hook-architecture.md`
- Modify: `docs/INDEX.md`

**Step 1: redigir o Hook Architecture Design Doc**
Conteudo:
1. **Principios de design** - definicao e fronteiras das tres categorias (security/gate/feedback)
2. **Convencoes de nome** - regras para nome de arquivo, nome de funcao e numeracao de Phase
3. **Registro panoramico de hooks** - eventos, tipos, responsabilidades, relacoes de chamada e local de registro de cada hook
4. **Contrato das libs compartilhadas** - API e regras de uso de cada arquivo em `_lib/`
5. **Regras dos shadow hooks** - como gerir scripts chamados internamente por outros hooks
6. **Fluxo para criar/alterar/depreciar hooks** - processo padrao de mudanca
7. **Regras de geracao de config** - generate_configs.py e a unica fonte de configs; edicao manual proibida
8. **Design de extensibilidade** - inclui:
   - **Arvore de decisao por categoria** - novo hook deve ir para security/, gate/ ou feedback/?
     ```
     Necessidade do novo hook
       ├── precisa bloquear operacao perigosa? → security/ (exit 2, bloqueio incondicional)
       ├── precisa bloquear fluxo nao conforme? → gate/ (exit 2, com bypass)
       └── prove feedback ou injeta contexto? → feedback/ (exit 0, advisory)
     ```
   - **Checklist do fluxo de novo hook** - passos completos da necessidade ao deployment:
     1. Decidir categoria (com a arvore de decisao)
     2. Escrever script em `hooks/<category>/`, source de `_lib/common.sh`
     3. Atualizar o registro em enforcement.md
     4. Atualizar generate_configs.py (incluir o hook na lista do agent correspondente)
     5. Rodar `python3 scripts/generate_configs.py` para regenerar config
     6. Rodar `python3 scripts/generate_configs.py --validate` para confirmar consistencia
     7. Adicionar testes em `tests/hooks/`
   - **Regras de extensao de _lib/** - novas funcoes compartilhadas (assinatura, documentacao, compatibilidade)
   - **Padrao de adesao para shadow hooks** - quando um hook pode chamar outro internamente e como anotar isso no registro
   - **Pontos de extensao de eventos** - os 4 eventos atuais (PreToolUse/PostToolUse/UserPromptSubmit/Stop) + reservas de extensao (ex.: como integrar quando o Kiro adicionar novos eventos como agentSpawn)
   - **Fluxo de deprecacao de hook** - passos para depreciar/remover:
     1. Em enforcement.md, marcar como `deprecated`, com motivo e alternativa
     2. Remover da generate_configs.py (config nao inclui mais o hook)
     3. Rodar `python3 scripts/generate_configs.py` para regenerar config
     4. Mover o script para `.trash/` (recuperavel), nunca apagar direto
     5. Limpar `.trash/` no proximo major release
   - **Relacao Source of Truth** - relacao entre enforcement.md (doc) e generate_configs.py (codigo):
     - enforcement.md e a **source of truth de design** (principios, fronteiras, relacao de chamada, regras de extensao)
     - generate_configs.py e a **source of truth de configuracao** (qual hook esta registrado em qual evento de qual agent)
     - `--validate` valida consistencia: hooks registrados em enforcement.md tem config correspondente no generator e vice-versa
     - Em caso de divergencia, vale enforcement.md (intencao humana de design); corrigir o generator

**Step 2: atualizar docs/INDEX.md**
Incluir o link para o Hook Architecture Doc.

**Verificação:**
```bash
# 验证 architecture doc 存在且包含关键 section（含扩展性）
test -f docs/designs/2026-02-18-hook-architecture.md && \
grep -q '## Design Principles' docs/designs/2026-02-18-hook-architecture.md && \
grep -q '## Hook Registry' docs/designs/2026-02-18-hook-architecture.md && \
grep -q '## Lifecycle' docs/designs/2026-02-18-hook-architecture.md && \
grep -q '## Extensibility' docs/designs/2026-02-18-hook-architecture.md
```

### Tarefa 6: fixacao via codigo - advisory em pre-write + obrigatoriedade do validate em generate_configs

**Arquivos:**
- Modify: `hooks/gate/pre-write.sh`

**Step 1: em gate_instruction_files, adicionar advisory para a pasta hooks/**
Modificar `gate_instruction_files()` para emitir um aviso (sem bloquear) quando o write atinge a pasta `hooks/`. Ao mexer em script de hook, o advisory lembra de atualizar enforcement.md e rodar generate_configs.py --validate.

Logica:
```
if FILE matches hooks/**/*.sh:
  echo "⚠️ Hook file modified. Remember to update enforcement.md and run generate_configs.py --validate" >&2
  # sem exit 2 - a coercao real e a Tarefa 7 com --validate
```

~~A proposta original (flag em /tmp para verificar se enforcement.md foi modificado) foi descartada. Motivo: o agent poderia editar uma linha qualquer de enforcement.md so para acionar a flag e depois mexer no hook, contornando a checagem. Substituida por advisory na escrita (leve) + validate forte no momento de gerar config (intransponivel).~~

**Verificação:**
```bash
# 验证 hooks/ 目录修改时有 advisory 提醒
echo '{"tool_name":"fs_write","tool_input":{"path":"hooks/security/block-dangerous.sh","file_text":"test","command":"str_replace"}}' | bash hooks/gate/pre-write.sh 2>&1 | grep -q 'Hook file modified'
```

### Tarefa 7: fixacao via codigo - generate_configs.py com validacao de consistencia

**Arquivos:**
- Modify: `scripts/generate_configs.py`

**Step 1: incluir o subcomando validate**
Adicionar o modo `--validate` em generate_configs.py:
- Varre todos os `.sh` em `hooks/` (excluindo `_lib/`)
- Compara com o registro em enforcement.md
- Reporta: scripts de hook nao registrados; entradas registradas cujo arquivo nao existe
- Exit code nao zero indica inconsistencia

**Step 2: rodar a validacao automaticamente ao gerar config**
Cada `python3 scripts/generate_configs.py` roda a validacao antes de gerar; se inconsistente, recusa gerar.

**Verificação:**
```bash
# 验证 validate 模式可用且当前状态一致
python3 scripts/generate_configs.py --validate
```

### Tarefa 8: melhorar qualidade do reviewer - reviewer-prompt.md com requisito de mostrar a analise

**Arquivos:**
- Modify: `agents/reviewer-prompt.md`

**Step 1: em Output Structure, incluir o bloco Evidence of Analysis**
Em `## Output Structure` de reviewer-prompt.md, antes de Findings, incluir uma secao `**Analysis trace:**` para o reviewer mostrar o raciocinio em vez de apenas a conclusao.

Regras a adicionar:
```markdown
## Output Quality Rules

1. **Show your work** — Every finding must include the analysis trace that led to it. 
   "APPROVE — all looks good" without listing what you checked = rubber stamp = violation.
2. **Per-item analysis for Verify Correctness** — Each verify command must have:
   - What it confirms
   - Exit code trace for correct implementation (show intermediate steps, not just "exit 0")
   - Exit code trace for broken implementation
   - Verdict: sound / false-positive / false-negative
   Skipping rows or writing "all sound" without per-row traces = review REJECTED.
3. **Scope check before every finding** — Before writing a finding, re-read the plan's 
   Non-Goals. If your finding addresses a Non-Goal, discard it silently.
4. **Fill the template** — When the dispatch query includes a table template, you MUST 
   copy it and fill every cell. Do not summarize, do not skip rows, do not replace the 
   table with prose. The template IS the minimum acceptable output.
```

**Step 2: reforcar a secao "What I checked"**
Em Output Structure, transformar `**What I checked and found no issues:**` em obrigatorio, com pelo menos 3 pontos verificados especificos (nao "checked code quality" generico).

**Verificação:**
```bash
# 验证 reviewer-prompt.md 包含 show-your-work 规则
grep -q 'Show your work' agents/reviewer-prompt.md && grep -q 'Per-item analysis' agents/reviewer-prompt.md
```

### Tarefa 9: melhorar qualidade do reviewer - planning skill descreve formato de output dos angles

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**Step 1: prescrever formato obrigatorio para o angle Verify Correctness**
Na tabela Fixed angles da planning skill, mudar a Mission de Verify Correctness para template prefixado + preenchimento obrigatorio:
```
For each checklist verify command, you MUST copy this table and fill in EVERY cell:

| # | Verify command | Confirms what | Exit code (correct impl) | Exit code (broken impl) | Sound? |
|---|---------------|---------------|--------------------------|--------------------------|--------|
| 1 | [copy from plan] | [fill] | [trace: ... → exit ?] | [trace: ... → exit ?] | [Y/N + reason] |
| 2 | ... | ... | ... | ... | ... |

Rules:
- EVERY row must show the shell execution trace, not just "exit 0" — show the intermediate steps
- If you skip a row or write "all sound" without per-row traces, your review is REJECTED
- Only flag commands where correct and broken give the SAME exit code
```
Ganho central: passar de "produza a tabela" para "copie a tabela e preencha", reduzindo a margem do reviewer cortar atalhos.

**Step 1b: prescrever template para Goal Alignment**
Mesma logica de template prefixado:
```
Copy and fill this table for EVERY task:

| Task # | Goal phrase served (quote exact words) | If removed, which Goal phrase loses coverage? |
|--------|---------------------------------------|----------------------------------------------|
| 1 | [quote] | [answer] |
| 2 | ... | ... |

Then copy and fill the coverage matrix:

| Goal phrase (copy from plan header) | Covered by Task #s |
|-------------------------------------|-------------------|
| [phrase 1] | [list] |
```

**Step 2: scope guard para Completeness**
Na Mission do angle Completeness, incluir:
```
SCOPE: Only analyze functions/branches in files that the plan MODIFIES (listed in Files: fields). 
Do NOT flag functions in files the plan merely reads or references. The plan is not obligated to 
test every function in every file it touches — only the functions it changes.
```

**Step 3: lembrete sobre Non-Goals para todos os random angles**
Abaixo do header da tabela do Random pool, incluir uma regra geral:
```
**All angles:** Before writing any finding, verify it is within the plan's stated Goal and 
NOT in Non-Goals. Findings outside scope are noise — discard silently.
```

**Verificação:**
```bash
# 验证 planning skill 包含 output format 和 scope guard
grep -q 'Exit code (correct impl)' skills/planning/SKILL.md && grep -q 'SCOPE:' skills/planning/SKILL.md
```

### Tarefa 10: atualizar o indice de knowledge

**Arquivos:**
- Modify: `knowledge/INDEX.md`

**Step 1: incluir o roteamento de Hook Architecture**
Na Routing Table de INDEX.md, adicionar entradas relacionadas a Hook Architecture.

**Verificação:**
```bash
# 验证 INDEX.md 包含 hook architecture 路由
grep -qi 'hook.*architecture\|hook.*design' knowledge/INDEX.md
```

## Review

### Round 1 (2026-02-18)

**Angles:** Goal Alignment + Verify Correctness + Completeness + Clarity

| Reviewer | Verdict | Key Findings |
|----------|---------|-------------|
| Goal Alignment | APPROVE | All goal phrases covered, execution order logical |
| Verify Correctness | APPROVE | 10 verify commands correct, no false positives (shallow review — no per-command trace) |
| Completeness | ~~REQUEST CHANGES~~ → Rejected | Flagged "zero coverage" for existing hook functions (gate_check, gate_brainstorm etc.) — outside Non-Goals scope. Plan is governance/audit, not rewrite/test-all |
| Clarity | APPROVE | All 8 tasks implementable from description alone |

**Calibration:** Completeness reviewer's findings rejected - plan explicitly states Non-Goals include "Sem refatorar pre-write.sh". Testing existing function logic is a separate work item.

**Review quality note:** Verify Correctness reviewer gave blanket APPROVE without per-command exit code traces. Goal Alignment was mechanical. Future rounds should demand structured evidence.

**Post-review additions:**
- Goal updated to include extensibility ("garantindo um fluxo claro para integrar hooks novos")
- Task 5 expanded with extensibility design: classification decision tree, new hook checklist, _lib extension rules, event extension points
- Task 8-9 added: reviewer quality fixes (show-your-work requirement, verify output format, scope guard)
- Checklist updated: +3 items for reviewer quality, +1 for extensibility section
- Original Task 8 renumbered to Task 10

**Root cause of review quality issues (3 layers):**
1. reviewer-prompt.md lacks "show your work" enforcement — reviewer can APPROVE without evidence
2. dispatch query Mission copied verbatim from planning skill angle table — too abstract for agent execution
3. Completeness angle mission has no scope guard — reviewer flags functions outside plan's modification scope

### Round 2 (2026-02-18)

**Angles:** Goal Alignment + Verify Correctness + Technical Feasibility + Testability

| Reviewer | Verdict | Quality | Key Findings |
|----------|---------|---------|-------------|
| Goal Alignment | APPROVE | ⬆️ Better — output coverage matrix, identified Task 4 as only removable item | Still somewhat mechanical |
| Verify Correctness | APPROVE | ❌ Still bad — blanket "all sound" without per-item trace despite explicit table requirement in query | Confirms Task 8+9 fixes are necessary |
| Technical Feasibility | APPROVE | ✅ Good — dependency table, 5 specific check points, no false findings | Structured output format worked |
| Testability | APPROVE with findings | ✅ Best — per-item false-negative analysis, found Task 6 advisory weakness | Over-flagged (all 13 "WEAK" assumes adversarial agent) but analysis method correct |

**Key insight from Round 2:** "produza a tabela" e ignorado; "copie a tabela e preencha cada celula" funciona. Verify Correctness precisa do template prefixado (Tarefa 9 reforcada). reviewer-prompt.md precisa da regra "Fill the template" (Tarefa 8 reforcada).

**Testability finding calibration:** All 13 verify marked "WEAK" because adversarial agent could create fake files. Rejected — verify commands assume honest execution, not adversarial bypass. But Task 6 advisory weakness is valid and already addressed by Socratic self-check (real enforcement is Task 7 validate).

**Verdict: APPROVE (with post-review enhancements)**

### Round 3 (2026-02-18) - template prefixado + preenchimento

**Angles:** Goal Alignment + Verify Correctness + Security + Compatibility & Rollback

| Reviewer | Verdict | Quality | Key Findings |
|----------|---------|---------|-------------|
| Goal Alignment | APPROVE | ⬆️ medio - identificou Task 5/7 como single point of failure, mas a tabela ainda nao foi totalmente preenchida | aceitavel |
| Verify Correctness | REQUEST CHANGES | ✅✅ otimo - tracou os 13 verify item a item; detectou false negative em #4 com sort -nu | **bug real, ja corrigido** |
| Security | REQUEST CHANGES | ✅ bom - data flow trace; 2 findings | P0 rejected (enforcement.md nao e entrada externa); P1 Nit |
| Compatibility & Rollback | APPROVE | ✅✅ otimo - busca por arquivo em tests/, preencheu a tabela completa | maior qualidade |

**Tratamento dos findings de Verify Correctness:**
- ✅ #4 false negative com sort -nu -> corrigido: removido o -u; verificacao de duplicatas adicionada
- ❌ #8 validate nao implementado -> Rejected: a Tarefa 7 e justamente implementar; o verify roda apos a implementacao

**Tratamento dos findings de Security:**
- ❌ P0 command injection em enforcement.md -> Rejected: enforcement.md e arquivo interno mantido por humanos, nao e entrada externa; o string matching em Python nao executa shell
- ❌ P1 path ANSI injection -> Nit: FILE vem de jq, nao ha caminho real para injecao

**Resumo da qualidade da review:** o uso de template prefixado elevou bastante a qualidade do angle Verify Correctness (do blanket APPROVE a descoberta de bug real). Compatibility & Rollback teve a maior qualidade (busca por arquivo + tabela completa). Goal Alignment ainda tem espaco para melhorar, mas e aceitavel.

**Verdict: APPROVE**

## Checklist

- [x] llm-eval.sh movido para .trash | `test ! -f hooks/_lib/llm-eval.sh && test -f .trash/llm-eval.sh`
- [x] enforcement.md contem todos os 15 hooks | `test $(grep -c '| .hooks/' .kiro/rules/enforcement.md) -ge 15`
- [x] settings.json contem enforce-ralph-loop | `jq -r '.. | .command? // empty' .claude/settings.json | grep -q 'enforce-ralph-loop'`
- [x] numeracao das Phases em pre-write.sh contigua e sem repeticoes | `grep -oE 'Phase [0-9]+' hooks/gate/pre-write.sh | awk '{print $2}' | sort -n | awk 'NR>1{if($1!=prev+1 || $1==prev){exit 1}}{prev=$1}'`
- [x] session-init.sh sem delegation reminder | `! grep -q 'Delegation:' hooks/feedback/session-init.sh`
- [x] Hook Architecture Doc existe e completo | `test -f docs/designs/2026-02-18-hook-architecture.md && grep -q '## Design Principles' docs/designs/2026-02-18-hook-architecture.md && grep -q '## Hook Registry' docs/designs/2026-02-18-hook-architecture.md && grep -q '## Lifecycle' docs/designs/2026-02-18-hook-architecture.md && grep -q '## Extensibility' docs/designs/2026-02-18-hook-architecture.md`
- [x] alteracoes em hooks/ disparam advisory | `echo '{"tool_name":"fs_write","tool_input":{"path":"hooks/security/block-dangerous.sh","file_text":"test","command":"str_replace"}}' | bash hooks/gate/pre-write.sh 2>&1 | grep -q 'Hook file modified'`
- [x] generate_configs.py --validate passa | `python3 scripts/generate_configs.py --validate`
- [x] docs/INDEX.md contem o roteamento de hook architecture | `grep -qi 'hook.*architecture\|hook.*design' docs/INDEX.md`
- [x] knowledge/INDEX.md contem o roteamento de hook architecture | `grep -qi 'hook.*architecture\|hook.*design' knowledge/INDEX.md`
- [x] reviewer-prompt.md contem as regras Show your work | `grep -q 'Show your work' agents/reviewer-prompt.md && grep -q 'Per-item analysis' agents/reviewer-prompt.md`
- [x] planning skill define o formato de output do verify | `grep -q 'Exit code (correct impl)' skills/planning/SKILL.md`
- [x] angle Completeness da planning skill tem scope guard | `grep -q 'SCOPE:' skills/planning/SKILL.md`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
