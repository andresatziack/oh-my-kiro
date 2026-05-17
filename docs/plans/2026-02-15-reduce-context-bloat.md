# Reduzir Inchaço de Contexto - Merge de Hook + Estratégia de Subagentes

**Objetivo:** Reduzir a velocidade de inflar a conversa e mitigar falhas de compaction do Kiro CLI. Mesclar hooks para diminuir mensagens e otimizar a estrategia de subagent para isolar trabalho pesado.

**Arquitetura:** Mesclar os 3 hooks de postToolUse em `post-write.sh`, mesclar os 3 de preToolUse em `pre-write.sh` (security hooks permanecem independentes). Adicionar regras de threshold para subagent na planning skill.

**Tech Stack:** Bash (hooks), Markdown (skill docs), JSON (agent config)

## Tarefas

### Tarefa 1: mesclar hooks postToolUse -> post-write.sh

Mesclar `auto-test.sh` + `auto-lint.sh` + `remind-update-progress.sh` em um unico arquivo `hooks/feedback/post-write.sh`.

**Arquivos:**
- Create: `hooks/feedback/post-write.sh`
- Modify: `.kiro/agents/default.json` (postToolUse passa a ter uma unica entrada)
- Modify: `.kiro/agents/implementer.json` (postToolUse sincronizado)

**Error handling:** cada funcao com try-catch independente, falha em uma nao afeta as outras. lint/remind falham silenciosamente, apenas falha de test sai com exit 1.

**Steps:**
1. Criar `post-write.sh` com tres funcoes: `run_lint`, `run_test`, `remind_progress`, cada uma capturando erros internamente
2. Atualizar `default.json` postToolUse de 3 entradas -> 1 entrada
3. Atualizar `implementer.json` postToolUse para refletir a mudanca
4. Testar: `echo '{"tool_name":"fs_write","tool_input":{"file_path":"test.ts"}}' | bash hooks/feedback/post-write.sh`

### Tarefa 2: mesclar hooks preToolUse -> pre-write.sh

Mesclar `require-workflow.sh` + `scan-skill-injection.sh` (em security/) + `inject-plan-context.sh` (em feedback/) em `hooks/gate/pre-write.sh`. Security hooks de execute_bash permanecem independentes.

**Arquivos:**
- Create: `hooks/gate/pre-write.sh`
- Modify: `.kiro/agents/default.json` (preToolUse fs_write de 3 entradas -> 1 entrada)

**Error handling:** falha do gate check (require-workflow) -> exit 2 (bloqueio forte). Falha do injection scan -> exit 2. Falha do plan context inject -> exit 0 silencioso (advisory).

**Steps:**
1. Criar `pre-write.sh` com tres fases sequenciais: gate check -> injection scan -> plan context inject
2. Atualizar `default.json` preToolUse
3. Testar: confirmar que sem plan ativo o gate ainda intercepta com exit 2

### Tarefa 3: atualizar planning skill - threshold de subagent

Adicionar regras de trigger de subagent na Phase 2 da estrategia de execucao em `skills/planning/SKILL.md`.

**Arquivos:**
- Modify: `skills/planning/SKILL.md`

**Steps:**
1. Adicionar no inicio da Phase 2 a regra de selecao da estrategia de execucao:
   - checklist <= 3 itens -> Strategy A (execucao sequencial na conversa principal)
   - checklist > 3 itens -> Strategy C (subagent por task)
   - 2+ tarefas independentes sem dependencia -> Strategy B (subagents em paralelo)
2. Manter as regras enxutas, no maximo 10 linhas

### Tarefa 4: limpar arquivos de hook antigos

Apos o merge concluido e validado, apagar os arquivos antigos.

**Arquivos:**
- Delete: `hooks/feedback/auto-test.sh`
- Delete: `hooks/feedback/auto-lint.sh`
- Delete: `hooks/feedback/remind-update-progress.sh`
- Delete: `hooks/feedback/inject-plan-context.sh`
- Delete: `hooks/gate/require-workflow.sh`
- Delete: `hooks/security/scan-skill-injection.sh`

**Steps:**
1. `grep -r 'auto-test\|auto-lint\|remind-update-progress\|inject-plan-context\|require-workflow\|scan-skill-injection' --include='*.json' --include='*.sh' --include='*.md' .` para confirmar que nao restam referencias
2. `git rm` nos arquivos antigos
3. Se aparecer referencia residual, corrigir antes de apagar

**Rollback:** todos os arquivos antigos podem ser recuperados via git, com `git checkout HEAD~1 -- hooks/feedback/auto-test.sh` (etc.).

## Review

### Round 1: REQUEST CHANGES (addressed)
~~Missing error handling, rollback, file location inconsistency, dependency verification.~~
All fixed in plan revision: error handling per-function, rollback via git history, correct file paths, grep verification step added.

### Round 2: APPROVE

**Round 1 Issues Resolution:**
✅ **Error handling:** Each function has independent error handling, lint/remind fail silently, only test failure exits 1
✅ **Rollback:** Git history rollback documented with specific commands
✅ **File location inconsistency:** Correct paths noted (scan-skill-injection in security/, inject-plan-context in feedback/)
✅ **Dependency verification:** grep step added before deletion to check for remaining references
✅ **No backup:** Git history serves as backup mechanism

**Critical:** None identified
**Warning:** None identified  
**Suggestion:** Plan is well-structured and addresses all previous concerns comprehensively

**Verdict: APPROVE** - All Round 1 issues properly resolved, implementation approach is sound

## Checklist

- [x] `hooks/feedback/post-write.sh` criado, com as tres funcoes lint + test + remind
- [x] `hooks/gate/pre-write.sh` criado, com workflow gate + injection scan + plan context
- [x] `default.json` postToolUse de 3 entradas -> 1 entrada
- [x] `default.json` preToolUse[fs_write] de 3 entradas -> 1 entrada
- [x] `implementer.json` postToolUse atualizado em sincronia
- [x] Security hooks (block-dangerous/block-secrets/block-sed-json) permanecem independentes
- [x] `skills/planning/SKILL.md` ganhou a regra de threshold de subagent
- [x] arquivos de hook antigos apagados, sem referencias residuais
- [x] gate check (exit 2 de bloqueio) continua valendo apos o merge
