# Framework v3: Reformulação Determinística

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Objetivo:** Refatorar o framework de agent usando comandos hardcoded + bloqueio forte em PreToolUse para garantir trigger deterministico; faxina agressiva no codigo e na estrutura, com compatibilidade dupla (Kiro + CC).

**Arquitetura:** Modelo deterministico de tres camadas - L1 camada de comando (usuario aciona o workflow completo), L2 camada de bloqueio (PreToolUse impede fluxos errados), L3 camada de feedback (PostToolUse/Stop dao informacao sem bloquear). Fonte unica de configuracao gerando configs para os dois plataformas.

**Tech Stack:** Bash hooks, jq, Kiro agents JSON, CC settings.json

**Affected Features:** todos - este e um rewrite a nivel de framework

---

## Phase 1: arquivar artefatos antigos + montar nova estrutura de pastas

### Tarefa 1.1: ponto de rollback via git tag + arquivamento

**Arquivos:**
- Create: `archive/v2/` (move old assets here)

**Step 1: criar ponto de rollback**
```bash
git tag v2-before-v3-overhaul
git push origin v2-before-v3-overhaul
```

**Step 2: arquivar artefatos nao essenciais**
```bash
mkdir -p archive/v2
mv docs/audit/ archive/v2/
mv docs/completed/ archive/v2/
mv docs/plans/2026-02-14-e2e-v3-test-framework.md archive/v2/
mv docs/plans/2026-02-14-adversarial-hook-audit.md archive/v2/
mv docs/research/ archive/v2/
mv tools/e2e-v3/ archive/v2/
mv tools/test-hooks.sh archive/v2/
mv plans/ archive/v2/
mv templates/ archive/v2/
```

**Step 3: limpar diretorios vazios e arquivos descontinuados**
```bash
rm -rf .claude/skills/self-reflect/{commands}
```

**Step 4: Commit**
```bash
git add -A && git commit -m "chore: archive v2 assets before v3 overhaul"
```

### Tarefa 1.2: montar a nova estrutura de pastas

**Estrutura desejada:**
```
.
├── AGENTS.md                    # 精简到 <60 行
├── CLAUDE.md                    # symlink → AGENTS.md
├── hooks/                       # 统一 hook 源码（不再分 .claude/.kiro）
│   ├── _lib/
│   │   ├── common.sh            # 共享函数（含跨平台兼容）
│   │   ├── patterns.sh          # 安全正则
│   │   └── llm-eval.sh          # LLM 调用
│   ├── security/
│   │   ├── block-dangerous.sh
│   │   ├── block-secrets.sh
│   │   ├── block-sed-json.sh
│   │   └── scan-skill-injection.sh  # 保留（reviewer E2）
│   ├── gate/                    # 新：硬拦截层
│   │   └── require-workflow.sh  # 核心：写代码前必须走流程
│   └── feedback/                # 合并 quality + lifecycle
│       ├── auto-test.sh
│       ├── auto-lint.sh
│       └── verify-completion.sh
├── skills/                      # 统一 skill 源码
│   ├── brainstorming/SKILL.md
│   ├── planning/SKILL.md        # 合并 writing-plans + executing-plans
│   ├── debugging/SKILL.md       # 重命名 systematic-debugging
│   ├── reviewing/SKILL.md       # 合并 code-review-expert + requesting/receiving-code-review
│   ├── research/SKILL.md
│   ├── self-reflect/SKILL.md
│   ├── verification/SKILL.md    # verification-before-completion
│   └── finishing/SKILL.md       # finishing-a-development-branch
├── agents/                      # 统一 agent 定义源码
│   ├── reviewer.md
│   ├── implementer.md
│   ├── debugger.md
│   └── researcher.md
├── commands/                    # 新：自定义命令（Kiro prompts 源）
│   ├── plan.md
│   ├── debug.md
│   ├── research.md
│   ├── review-code.md
│   └── review-plan.md
├── scripts/                     # 新：构建/生成脚本
│   └── generate-platform-configs.sh
├── .claude/                     # 生成的 CC 配置（由脚本生成）
│   ├── settings.json
│   ├── rules/                   # 保留
│   ├── hooks -> ../hooks        # symlink
│   └── skills -> ../skills      # symlink
├── .kiro/                       # 生成的 Kiro 配置（由脚本生成）
│   ├── agents/                  # 生成的 JSON
│   ├── prompts -> ../commands   # symlink
│   ├── hooks -> ../hooks        # symlink
│   ├── skills -> ../skills      # symlink
│   └── rules/                   # 保留
├── knowledge/
│   ├── INDEX.md
│   ├── lessons-learned.md       # 保留
│   └── product/PRODUCT.md
└── docs/
    ├── INDEX.md
    ├── designs/                  # 保留设计文档
    └── plans/                    # 活跃 plan
```

**Step 1: criar pastas novas**
```bash
mkdir -p hooks/_lib hooks/security hooks/gate hooks/feedback
mkdir -p skills agents commands scripts
```

**Step 2: mover hooks fonte para o local unificado**
```bash
cp .claude/hooks/_lib/* hooks/_lib/
cp .claude/hooks/security/block-dangerous-commands.sh hooks/security/block-dangerous.sh
cp .claude/hooks/security/block-secrets.sh hooks/security/block-secrets.sh
cp .claude/hooks/security/block-sed-json.sh hooks/security/block-sed-json.sh
cp .claude/hooks/security/scan-skill-injection.sh hooks/security/scan-skill-injection.sh
cp .claude/hooks/quality/auto-test.sh hooks/feedback/auto-test.sh
cp .claude/hooks/quality/auto-lint.sh hooks/feedback/auto-lint.sh
cp .claude/hooks/quality/verify-completion.sh hooks/feedback/verify-completion.sh
cp .claude/hooks/autonomy/context-enrichment.sh hooks/feedback/context-enrichment.sh
```

**Step 3: criar os symlinks**
```bash
# 删除旧的 .kiro symlinks
rm -f .kiro/skills .kiro/hooks

# 新 symlinks
ln -sf ../hooks .claude/hooks
ln -sf ../hooks .kiro/hooks
ln -sf ../skills .claude/skills
ln -sf ../skills .kiro/skills
ln -sf ../commands .kiro/prompts
```

**Step 4: Commit**
```bash
git add -A && git commit -m "refactor: establish v3 unified directory structure"
```

---

## Matriz de migracao de Hooks

| v2 Hook | Destino v3 | Observacao |
|---------|---------|------|
| `security/block-dangerous-commands.sh` | `security/block-dangerous.sh` | Renomear, logica inalterada |
| `security/block-secrets.sh` | `security/block-secrets.sh` | Inalterado |
| `security/block-sed-json.sh` | `security/block-sed-json.sh` | Inalterado |
| `security/scan-skill-injection.sh` | `security/scan-skill-injection.sh` | Mantido; path atualizado |
| `quality/enforce-skill-chain.sh` | `gate/require-workflow.sh` | Reescrito, logica simplificada |
| `quality/auto-test.sh` | `feedback/auto-test.sh` | Movido; corrigir chamada de stat |
| `quality/auto-lint.sh` | `feedback/auto-lint.sh` | Movido, inalterado |
| `quality/verify-completion.sh` | `feedback/verify-completion.sh` | Enxuto |
| `quality/enforce-tests.sh` | ~~descontinuado~~ | TaskCompleted so de CC; verify-completion ja cobre |
| `quality/reviewer-stop-check.sh` | mesclado ao stop hook do reviewer agent | virar echo inline |
| `autonomy/context-enrichment.sh` | `feedback/context-enrichment.sh` | Enxuto |
| `autonomy/auto-approve-safe.sh` | ~~descontinuado~~ | PermissionRequest so de CC; configurar direto em settings.json |
| `autonomy/inject-subagent-rules.sh` | ~~descontinuado~~ | SubagentStart so de CC; regras vao para o prompt do agent |
| `lifecycle/session-init.sh` | ~~descontinuado~~ | Funcionalidade migrada para context-enrichment |
| `lifecycle/session-cleanup.sh` | ~~descontinuado~~ | Sem funcao real |
| `_lib/common.sh` | `_lib/common.sh` | Funcoes cross-platform reforcadas |
| `_lib/llm-eval.sh` | `_lib/llm-eval.sh` | Inalterado |
| `_lib/patterns.sh` | `_lib/patterns.sh` | Inalterado |

## Phase 2: reescrever o mecanismo de bloqueio principal (require-workflow.sh)

### Tarefa 2.1: reescrever common.sh - compatibilidade cross-platform

**Arquivos:**
- Create: `hooks/_lib/common.sh`

**Melhorias principais:**
- Implementacao de `file_mtime()`:
```bash
file_mtime() {
  local f="$1"
  if [[ "$(uname)" == "Darwin" ]]; then
    stat -f %m "$f" 2>/dev/null || echo 0
  else
    stat -c %Y "$f" 2>/dev/null || echo 0
  fi
}
```
- `hook_block()` mantido
- `detect_test_command()` mantido
- ~~Adicionar workflow_state_file()~~ ~~descartado: o reviewer apontou race condition ao usar arquivo JSON em /tmp~~
- Em vez disso, checar diretamente os arquivos sob `docs/plans/` (sem estado, so verificacao no filesystem)

### Tarefa 2.2: criar require-workflow.sh - hook central de bloqueio

**Arquivos:**
- Create: `hooks/gate/require-workflow.sh`

**Logica de descoberta do Plan (resolve reviewer C3):**
```bash
find_active_plan() {
  # 找最近修改的 plan 文件，时间窗口内（可配置，默认 4h）
  local WINDOW="${WORKFLOW_PLAN_WINDOW:-14400}"  # 4h in seconds
  local NOW=$(date +%s)
  local LATEST=""
  local LATEST_MTIME=0

  for f in docs/plans/*.md; do
    [ -f "$f" ] || continue
    local mt=$(file_mtime "$f")
    if [ $((NOW - mt)) -lt "$WINDOW" ] && [ "$mt" -gt "$LATEST_MTIME" ]; then
      LATEST="$f"
      LATEST_MTIME="$mt"
    fi
  done

  # fallback: .completion-criteria.md
  if [ -z "$LATEST" ] && [ -f ".completion-criteria.md" ]; then
    local mt=$(file_mtime ".completion-criteria.md")
    if [ $((NOW - mt)) -lt "$WINDOW" ]; then
      LATEST=".completion-criteria.md"
    fi
  fi

  echo "$LATEST"
}
```

**Logica completa:**
```
Quando PreToolUse[Write|Edit|fs_write] dispara:
1. Nao e arquivo de codigo-fonte -> pass
2. E arquivo de teste -> pass (TDD permite escrever teste primeiro)
3. E str_replace/Edit (alteracao pequena) -> pass
4. .skip-plan existe -> pass (bypass)
5. find_active_plan() encontra plan ativo:
   a. Nao encontrou -> BLOCK "precisa criar um plan"
   b. Encontrou -> checar a secao ## Review:
      - Conteudo < 3 linhas -> BLOCK "precisa de revisao do reviewer"
      - Veredito REJECT/REQUEST CHANGES -> BLOCK "plan rejeitado"
   c. pass
```

**Janela de tempo:** ~~2h~~ -> 4h (configuravel via variavel de ambiente `WORKFLOW_PLAN_WINDOW`; sugestao do reviewer W1)

### Tarefa 2.3: reescrever context-enrichment.sh - reduzir a deteccao de correcao + lembrete de retomada

**Arquivos:**
- Create: `hooks/feedback/context-enrichment.sh`

**Mudancas:**
- Remover toda logica de "lembrete suave" (provada inutil)
- Manter apenas tres funcoes deterministicas:
  1. Deteccao de correcao -> escrever flag (o stop hook le)
  2. Lembrete de retomar tarefa nao concluida (.completion-criteria.md)
  3. Injecao de lessons de alta frequencia (texto hardcoded)
- Sem tentar classificar intencao ou rotear workflow (isso fica na camada de comandos)

### Tarefa 2.4: reescrever verify-completion.sh - reduzir o stop hook

**Arquivos:**
- Create: `hooks/feedback/verify-completion.sh`

**Mudancas:**
- Phase B (checagens deterministicas) preservada: completion-criteria + execucao de testes
- Phase A (LLM eval) preservada com prompt simplificado
- Phase C (loop de feedback) reduzida: so checar a flag de correcao + lembrar de atualizar lessons-learned
- Remover o uso redundante de `grep -c ... || true`; padronizar com `grep ... | wc -l`
- Tratamento de JSON corrompido: nao usar mais arquivo JSON de estado (sugestao reviewer E3)

---

## Phase 3: consolidacao das skills

### Tarefa 3.1: mesclar a planning skill

**Arquivos:**
- Create: `skills/planning/SKILL.md`

**Origens da fusao:**
- `writing-plans/SKILL.md` + `executing-plans/SKILL.md`
- Uma unica skill cobre as duas fases ("escrever plan" e "executar plan")
- Remover templates e exemplos redundantes; manter apenas o fluxo central

### Tarefa 3.2: mesclar a reviewing skill

**Arquivos:**
- Create: `skills/reviewing/SKILL.md`

**Origens da fusao:**
- `code-review-expert/SKILL.md` + `requesting-code-review/SKILL.md` + `receiving-code-review/SKILL.md`
- Uma skill cobrindo os tres papeis: solicitar review, executar review, receber review

### Tarefa 3.3: simplificar as demais skills

**Manter e renomear:**
- `brainstorming/` -> sem mudanca
- `systematic-debugging/` -> `debugging/`
- `verification-before-completion/` -> `verification/`
- `finishing-a-development-branch/` -> `finishing/`
- `self-reflect/` -> sem mudanca
- `research/` -> sem mudanca

**Remover - destino do conteudo (resolve reviewer C4):**

| Skill removida | Conteudo central | Mesclar em |
|-----------|---------|--------|
| `dispatching-parallel-agents` | Padrao de dispatch paralelo, criterios de independencia | `planning/SKILL.md` -> secao "Opcoes de execucao > modo paralelo" |
| `subagent-driven-development` | Um subagent por task + review | `planning/SKILL.md` -> secao "Opcoes de execucao > modo subagent" |
| `using-git-worktrees` | Criacao/limpeza de worktree | `planning/SKILL.md` -> secao "Preparacao > workspace isolado" |
| `test-driven-development` | Fluxo TDD red-green-refactor | `planning/SKILL.md` -> secao "Estrutura da Task > template de passos TDD" |
| `writing-clearly-and-concisely` | Regras de escrita Strunk | `knowledge/reference/writing-style.md` (arquivar) |
| `find-skills` | Logica de descoberta de skill | Manter como skill independente (facilita extensao futura) |
| `skill-creator` | Guia para criar skill | `knowledge/reference/skill-creation-guide.md` (arquivar) |
| `doc-coauthoring` | Fluxo de coautoria de docs | `knowledge/reference/doc-coauthoring.md` (arquivar) |
| `humanizer` | Remover marcas de IA na escrita | `knowledge/reference/humanizer.md` (arquivar) |
| `mermaid-diagrams` | Sintaxe Mermaid | `knowledge/reference/mermaid-diagrams.md` (arquivar) |
| `java-architect` | Arquitetura Spring Boot | `knowledge/reference/java-architect.md` (arquivar) |
| `requesting-code-review` | Fluxo para solicitar review | `reviewing/SKILL.md` -> secao "Solicitar Review" |
| `receiving-code-review` | Fluxo para receber review | `reviewing/SKILL.md` -> secao "Receber Review" |
| Reference de `code-review-expert` | Checklist SOLID | `reviewing/reference.md` (manter como referencia) |

**Lista final de skills (9):**
1. `brainstorming` - explorar requisitos
2. `planning` - escrever plan + executar plan + template TDD + estrategia paralela
3. `reviewing` - review de codigo/plan (solicitar + executar + receber)
4. `debugging` - debugging sistematico
5. `verification` - verificacao antes de concluir
6. `finishing` - finalizacao de branch
7. `self-reflect` - self-learning
8. `research` - research
9. `find-skills` - descoberta de skill (mantida para extensao)

### Tarefa 3.4: Commit
```bash
git add -A && git commit -m "refactor: consolidate 22 skills → 8 core skills"
```

---

## Phase 4: reescrever a camada de comandos

### Tarefa 4.1: reescrever o comando plan

**Arquivos:**
- Create: `commands/plan.md`

**Cadeia completa hardcoded:**
```markdown
You MUST follow this exact sequence. Do NOT skip or reorder any step.

## Step 1: Read skills/brainstorming/SKILL.md, explore requirements with user
## Step 2: Read skills/planning/SKILL.md, write plan to docs/plans/<date>-<slug>.md
## Step 3: Dispatch reviewer subagent to challenge the plan
## Step 4: If REJECT/REQUEST CHANGES → fix → re-review → repeat until APPROVE
## Step 5: Show final plan, ask user to confirm
## Step 6: Only after confirmation → execute plan per skills/planning/SKILL.md
```

(Mesma logica do v2; apenas atualizando os paths para a nova estrutura)

### Tarefa 4.2: reescrever o comando debug

**Arquivos:**
- Create: `commands/debug.md`

**Hardcoded:**
```markdown
## Step 1: Read skills/debugging/SKILL.md
## Step 2: Check knowledge/lessons-learned.md for known issues
## Step 3: Follow debugging methodology (reproduce → hypothesize → verify → fix)
```

### Tarefa 4.3: reescrever o comando research

**Arquivos:**
- Create: `commands/research.md`

### Tarefa 4.4: reescrever os comandos review-code / review-plan

**Arquivos:**
- Create: `commands/review-code.md`
- Create: `commands/review-plan.md`

### Tarefa 4.5: Commit
```bash
git add -A && git commit -m "refactor: rewrite command layer with hardcoded step chains"
```

---

## Phase 5: geracao de configuracao por plataforma

### Tarefa 5.1: criar o script de geracao de config

**Arquivos:**
- Create: `scripts/generate-platform-configs.sh`

**Funcoes:**
- Le os diretorios `hooks/`, `agents/`, `commands/`
- Gera `.claude/settings.json` (formato CC)
- Gera `.kiro/agents/*.json` (formato Kiro)
- Fonte unica da verdade; nao precisa mais manter duas versoes manualmente

**Logica para gerar CC settings.json:**
```bash
jq -n '{
  permissions: {allow: ["Bash(*)", "Read(*)", "Write(*)", "Edit(*)"], deny: []},
  hooks: {
    UserPromptSubmit: [{hooks: [{type: "command", command: "bash hooks/feedback/context-enrichment.sh"}]}],
    PreToolUse: [
      {matcher: "Bash", hooks: [
        {type: "command", command: "bash hooks/security/block-dangerous.sh"},
        {type: "command", command: "bash hooks/security/block-secrets.sh"},
        {type: "command", command: "bash hooks/security/block-sed-json.sh"}
      ]},
      {matcher: "Write|Edit", hooks: [
        {type: "command", command: "bash hooks/gate/require-workflow.sh"},
        {type: "command", command: "bash hooks/security/scan-skill-injection.sh"}
      ]}
    ],
    PostToolUse: [{matcher: "Write|Edit", hooks: [
      {type: "command", command: "bash hooks/feedback/auto-test.sh"},
      {type: "command", command: "bash hooks/feedback/auto-lint.sh"}
    ]}],
    Stop: [{hooks: [{type: "command", command: "bash hooks/feedback/verify-completion.sh"}]}]
  }
}' > .claude/settings.json
```

**Logica para gerar Kiro agents JSON:**
- Ler a definicao do agent em `agents/*.md` (name, description, tools, resources)
- Mapear de `hooks/` para o formato de hook do Kiro
- Gravar em `.kiro/agents/*.json`

### Tarefa 5.2: rodar o script e validar a configuracao

```bash
bash scripts/generate-platform-configs.sh
# 验证生成的文件
jq . .claude/settings.json
jq . .kiro/agents/default.json
```

### Tarefa 5.3: Commit
```bash
git add -A && git commit -m "feat: single-source config generation for CC + Kiro"
```

---

## Phase 6: enxugar AGENTS.md + atualizar knowledge

### Tarefa 6.1: reescrever AGENTS.md

**Meta: <60 linhas, manter apenas:**
- Identity (2 linhas)
- Verification First (3 linhas)
- Workflow (3 linhas)
- Skill Routing (tabela com as 8 skills)
- Knowledge Retrieval (3 linhas)
- Self-Learning (3 linhas)
- Shell Safety (3 linhas)
- Referencias para rules/ e enforcement.md

**Remover:**
- Plan as Living Document (ja garantido pela camada de comandos via hardcode)
- Compound Interest com explicacao detalhada (mover para reference.md)
- Long-Running Tasks com explicacao detalhada (mover para reference.md)

### Tarefa 6.2: atualizar knowledge/INDEX.md

Atualizar a tabela de roteamento para os novos paths.

### Tarefa 6.3: atualizar knowledge/lessons-learned.md

Adicionar registro do refactor v3 como win.

### Tarefa 6.4: Commit
```bash
git add -A && git commit -m "docs: streamline AGENTS.md and update knowledge index"
```

---

## Phase 6.5: testes comparativos da migracao (resolve reviewer M2)

### Tarefa 6.5.1: comparar comportamento do hook antigo e do novo

Submeter o mesmo input para os hooks antigo e novo, garantindo que o comportamento e identico:

```bash
# 准备测试输入
BLOCK_INPUT='{"tool_name":"fs_write","tool_input":{"file_path":"src/app.ts","command":"create"}}'
PASS_INPUT='{"tool_name":"fs_write","tool_input":{"file_path":"src/app.ts","command":"str_replace","old_str":"a","new_str":"b"}}'
TEST_INPUT='{"tool_name":"fs_write","tool_input":{"file_path":"src/__tests__/app.test.ts","command":"create"}}'

# 对比 enforce-skill-chain vs require-workflow（无 plan 时都应 block create）
echo "$BLOCK_INPUT" | bash .claude/hooks/quality/enforce-skill-chain.sh; echo "v2 exit: $?"
echo "$BLOCK_INPUT" | bash hooks/gate/require-workflow.sh; echo "v3 exit: $?"

# str_replace 都应 pass
echo "$PASS_INPUT" | bash .claude/hooks/quality/enforce-skill-chain.sh; echo "v2 exit: $?"
echo "$PASS_INPUT" | bash hooks/gate/require-workflow.sh; echo "v3 exit: $?"

# test 文件都应 pass
echo "$TEST_INPUT" | bash .claude/hooks/quality/enforce-skill-chain.sh; echo "v2 exit: $?"
echo "$TEST_INPUT" | bash hooks/gate/require-workflow.sh; echo "v3 exit: $?"
```

---

## Phase 7: validacao end-to-end

### Tarefa 7.1: validar funcionalidade dos hooks

```bash
# 测试 block-dangerous.sh
echo '{"tool_name":"execute_bash","tool_input":{"command":"rm -rf /"}}' | bash hooks/security/block-dangerous.sh

# 测试 block-sed-json.sh
echo '{"tool_name":"execute_bash","tool_input":{"command":"sed -i s/a/b/ config.json"}}' | bash hooks/security/block-sed-json.sh

# 测试 require-workflow.sh（无 plan 时应 block）
echo '{"tool_name":"fs_write","tool_input":{"file_path":"src/app.ts","command":"create"}}' | bash hooks/gate/require-workflow.sh

# 测试 require-workflow.sh（有 plan + review 时应 pass）
# 先创建一个带 review 的 plan，再测试
```

### Tarefa 7.2: validar a geracao de configuracao

```bash
bash scripts/generate-platform-configs.sh
# 验证 JSON 合法
jq . .claude/settings.json > /dev/null && echo "CC config OK"
jq . .kiro/agents/default.json > /dev/null && echo "Kiro config OK"
jq . .kiro/agents/reviewer.json > /dev/null && echo "Reviewer config OK"
```

### Tarefa 7.3: validar os symlinks

```bash
# 验证所有 symlink 指向正确
ls -la .claude/hooks  # → ../hooks
ls -la .claude/skills # → ../skills
ls -la .kiro/hooks    # → ../hooks
ls -la .kiro/skills   # → ../skills
ls -la .kiro/prompts  # → ../commands
```

### Tarefa 7.4: validar a integridade das skills

```bash
# 验证 9 个 skill 都有 SKILL.md 且有 frontmatter
for skill in brainstorming planning reviewing debugging verification finishing self-reflect research find-skills; do
  if [ -f "skills/$skill/SKILL.md" ] && head -1 "skills/$skill/SKILL.md" | grep -q '^---'; then
    echo "✅ $skill"
  else
    echo "❌ $skill MISSING or no frontmatter"
  fi
done
```

### Tarefa 7.5: commit final + tag

```bash
git add -A && git commit -m "feat: framework v3 — deterministic overhaul complete"
git tag v3.0.0
```

---

## Lista de remocoes (confirmacao)

| Item removido | Motivo |
|--------|------|
| `.claude/hooks/` (arquivos originais) | Movido para `hooks/`; .claude/hooks vira symlink |
| `.claude/skills/` (arquivos originais) | Movido para `skills/`; .claude/skills vira symlink |
| `.kiro/agents/prompts/` | prompts dos agents foram unificados em `agents/*.md` |
| `.kiro/rules/commands.md` | Definicoes de comando movidas para `commands/` |
| `plans/`, `templates/` | Diretorios vazios |
| 13 skills consolidadas/removidas | Ver Tarefa 3.3 (find-skills foi mantida) |
| `docs/audit/`, `docs/completed/`, `docs/research/` | Arquivar em `archive/v2/` |
| `tools/e2e-v3/`, `tools/test-hooks.sh` | Arquivar em `archive/v2/` |

## Riscos

| Risco | Mitigacao |
|------|------|
| Apos arquivar surge necessidade de arquivos antigos | git tag v2-before-v3-overhaul permite restaurar a qualquer momento |
| Novo require-workflow.sh bloqueia indevidamente | Bypass via .skip-plan + modo HOOKS_DRY_RUN |
| Bug no script de geracao de config | Validacao via jq apos a geracao + diff manual |
| Perda de conteudo na consolidacao de skill | Verificar item a item os fluxos centrais das skills originais (ver mapeamento na Tarefa 3.3) |

## Procedimento de rollback (resolve reviewer M1)

Se o v3 apresentar problema serio:
```bash
# 1. Voltar para o v2
git stash  # 保存当前未提交的改动
git checkout v2-before-v3-overhaul

# 2. Continuar trabalhando a partir do v2
git checkout -b hotfix-from-v2 v2-before-v3-overhaul

# 3. Se for confirmado o abandono do v3
git branch -D main  # 或 git reset --hard v2-before-v3-overhaul
```

## Formato Markdown da definicao de Agent (resolve reviewer M3)

Formato dos arquivos `agents/*.md`:
```markdown
---
name: reviewer
description: "Review expert. Read-only."
tools: [read, shell]
resources:
  - file://AGENTS.md
  - skill://skills/reviewing/SKILL.md
---

# Reviewer Agent

[System prompt content here]
```

O frontmatter YAML define o metadata; o corpo e o system prompt do agent.
`generate-platform-configs.sh` parseia o frontmatter para gerar o JSON.

## Compatibilidade reversa (resolve reviewer M4)

- `.completion-criteria.md` - inalterado; require-workflow.sh e verify-completion.sh suportam
- Plans ativos em `docs/plans/` - inalterados; o novo hook e compativel direto
- `knowledge/lessons-learned.md` - inalterado
- Variaveis de ambiente (`HOOKS_DRY_RUN`, `KIRO_EVAL_*`) - inalteradas

## Review

<!-- Reviewer: write your review here -->

### ADVERSARIAL REVIEW - 2026-02-14

**Categorização:** Foram encontradas issues CRÍTICAS, REQUEST CHANGES obrigatório.

#### PONTOS FORTES
- Modelo determinístico claro de três camadas (L1 commands, L2 PreToolUse blocks, L3 feedback)
- Geração de config a partir de fonte única elimina o ônus de manutenção dupla
- Consolidação agressiva de 22 -> 8 skills ataca o inchaço de complexidade
- Ponto de rollback via git tag oferece rede de segurança
- Estratégia de symlink mantém compatibilidade reversa durante a transição

#### ISSUES CRÍTICAS

**C1: Estratégia de migração de hook ausente**
```bash
# Plan shows copying hooks but missing critical ones:
cp .claude/hooks/quality/auto-test.sh hooks/feedback/auto-test.sh
# ❌ Missing: enforce-skill-chain.sh, reviewer-stop-check.sh, enforce-tests.sh
```
Esses hooks contêm lógica de negócio que será perdida. O plan precisa especificar quais hooks serão depreciados vs. mesclados em novos hooks.

**C2: Race conditions no estado de workflow**
```bash
# /tmp/agent-workflow-<project-hash>.json
# ❌ Multiple agent instances will corrupt this file
```
Sem mecanismo de file locking. Agentes concorrentes (reviewer + implementer) vão criar race conditions. Precisa de operações atômicas ou arquivos de estado por agente.

**C3: Lacunas de lógica em require-workflow.sh**
```
5. Checar estado do workflow:
   a. Algum plan criado nas ultimas 2h? Se nao -> BLOCK
```
❌ E se o plan existir mas estiver obsoleto (>2h)? E se múltiplos plans existirem? A lógica não trata a descoberta do arquivo de plan - qual plan checar?

**C4: Risco de perda de dados na consolidação de skills**
O plan deleta 14 skills mas a estratégia de merge é vaga:
- `test-driven-development` -> para onde vai a metodologia de TDD?
- `dispatching-parallel-agents` -> "merge na planning skill" mas sem mapeamento concreto
- `using-git-worktrees` -> "reduzido a um passo da planning skill" perde conhecimento especializado

#### WARNINGS

**W1: Janela de 2 horas é agressiva demais**
```
# 时间窗口从 24h 缩短到 2h（更紧凑）
```
Sessões reais de desenvolvimento muitas vezes ultrapassam 2h. Isso vai criar bloqueios falsos em sessões longas legítimas de coding.

**W2: Script de geração de configuração ausente**
A Tarefa 5.1 descreve a funcionalidade do `generate-platform-configs.sh` mas não fornece implementação. Mostra lógica jq complexa, mas sem tratamento de erro, validação ou cobertura de casos de borda.

**W3: Fragilidade na dependência de symlink**
```bash
ln -sf ../hooks .claude/hooks
ln -sf ../skills .claude/skills
```
Symlinks relativos quebram se os diretórios forem movidos. Precisa de paths absolutos ou validação.

#### COMPONENTES CRÍTICOS FALTANDO

**M1: Procedimento de rollback**
O plan cria git tag mas não traz instruções de rollback. E se o v3 quebrar a produção? Precisa de processo de restauração passo a passo.

**M2: Testes de migração**
Sem testes do comportamento dos hooks durante a transição. Precisa verificar que o novo `require-workflow.sh` produz os mesmos blocks/passes que o antigo `enforce-skill-chain.sh` em cenários reais.

**M3: Formato de definição de agente**
```
- Ler de `agents/*.md` a definicao do agent (name, description, tools, resources)
```
Sem especificação do formato markdown. Como tools/resources são codificados? Qual o schema?

**M4: Plano de compatibilidade reversa**
O que acontece com arquivos `.completion-criteria.md` existentes? Estado de workflow existente? O plan assume clean slate, mas sistemas reais têm estado persistente.

#### CASOS DE BORDA NÃO ENDEREÇADOS

**E1: Chamadas stat() multi-plataforma**
```bash
# Adicionar funcao file_mtime() unificando diferencas de stat entre macOS/Linux
```
O plan menciona isso mas não mostra a implementação. macOS usa `stat -f %m`, Linux usa `stat -c %Y`. Falta a implementação = hooks quebrados.

**E2: Vetor de ataque por skill injection**
O plan remove `scan-skill-injection.sh` dos hooks de security mas não explica por que esse vetor de ataque deixou de ser relevante.

**E3: Tratamento de corrupção de JSON**
O estado de workflow usa jq mas sem tratamento de arquivos JSON corrompidos. Um único write ruim quebra a detecção de workflow inteira.

#### VEREDITO: REQUEST CHANGES

**Correções obrigatórias antes da aprovação:**

1. **Adicionar matriz de migração de hooks** - mapeamento explícito de quais hooks v2 -> hooks v3, quais são depreciados
2. **Implementar file locking** para o estado de workflow ou usar arquivos por agente  
3. **Definir lógica de descoberta de plan** - como require-workflow.sh acha o arquivo de plan relevante
4. **Fornecer mapeamentos concretos de merge de skill** - para onde vai o conteúdo de cada skill deletada?
5. **Implementar generate-platform-configs.sh** com tratamento de erro
6. **Adicionar procedimento de rollback** com instruções passo a passo
7. **Especificar o schema markdown de definição de agente**
8. **Mostrar implementação de file_mtime()** para compatibilidade multi-plataforma

**Mudanças recomendadas:**
- Aumentar a janela para 4h ou torná-la configurável
- Adicionar fase de teste de migração antes da Phase 7
- Usar symlinks absolutos ou adicionar validação
- Adicionar lógica de recuperação de corrupção de JSON

Este é um refactor de alto risco e alta recompensa. A abordagem determinística é sólida, mas lacunas de execução podem quebrar o framework inteiro. Conserte issues críticas antes de prosseguir.
