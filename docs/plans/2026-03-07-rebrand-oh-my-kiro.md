# Rebrand oh-my-claude-code -> oh-my-kiro + Remoção do Suporte a Claude Code

**Objetivo:** Renomear o projeto de oh-my-claude-code (OMCC) para oh-my-kiro (OMK), remover todo o suporte à plataforma Claude Code e garantir que projetos downstream (GTM) possam migrar suavemente via submodule + ferramentas de sync atualizadas.

**Não-Objetivos:**
- Renomear o repositório no GitHub (o usuário faz isso manualmente)
- Modificar documentos históricos em archive/ ou docs/plans/ (preservar o histórico como está)
- Alterar arquivos do projeto GTM diretamente (o GTM faz re-sync via tool de sync atualizada)
- Reescrever lógica de hook/skill - apenas renomear referências e remover code paths específicos de CC

**Arquitetura:** Abordagem em três fases: (1) Remover todos os artefatos de Claude Code (.claude/, CLAUDE.md, code paths específicos de CC, testes de integração CC), (2) Renomear OMCC->OMK em todo o código ativo e docs (arquivo de overlay, tool de sync, tool de init, generate_configs, README, AGENTS.md, knowledge/INDEX.md), (3) Adicionar shim de backward-compat para que o `.omcc-overlay.json` existente do GTM ainda funcione durante a migração.

**Tech Stack:** bash, python3 (sed/rename em lote), git

**Diretório de Trabalho:** `.`

## Tarefas

### Tarefa 1: Remover Artefatos do Claude Code

**Arquivos:**
- Delete: `.claude/` (diretório inteiro incluindo symlinks)
- Delete: `CLAUDE.md`
- Delete: `tests/cc-integration/` (diretório inteiro)
- Delete: `tests/hooks/test-cc-compat.sh`
- Delete: `knowledge/claude-code-research.md`
- Delete: `docs/claude-code-gap-analysis.md`
- Delete: `docs/kiro-hook-compatibility.md`

**O que implementar:**
Remover todos os arquivos específicos do Claude Code. `.claude/hooks` e `.claude/skills` são symlinks - removê-los não afeta os diretórios reais. `.claude/rules/` tem regras específicas de CC com equivalentes em `.kiro/rules/`. `.claude/agents/` tem agents em formato CC markdown - o Kiro usa `.kiro/agents/*.json`.

**Verificação:** `test ! -d .claude && test ! -f CLAUDE.md && test ! -d tests/cc-integration && echo OK`

---

### Tarefa 2: Remover Code Paths de CC dos Scripts Python

**Arquivos:**
- Modify: `scripts/generate_configs.py` - remover funções `cc_*`, `claude_settings()`, geração de markdown de agent CC, paths de saída `.claude/`
- Modify: `scripts/lib/cli_detect.py` - remover detecção de CLI claude, manter apenas kiro-cli + override por env
- Modify: `tests/test_generate_configs.py` - remover casos de teste específicos de CC
- Modify: `tests/ralph-loop/test_ralph_loop.py` - remover `test_detect_claude_cli`, atualizar referências CC
- Modify: `tests/test_debugging_rules.py` - remover testes `test_claude_rules_*`

**O que implementar:**
Remover todos os code paths do Claude Code. `generate_configs.py` gera tanto configs CC quanto Kiro - remover a metade CC. `cli_detect.py` tenta claude primeiro - remover claude, tornar kiro-cli primário após o override por env.

**Verificação:** `! grep -q 'def cc_\|def claude_settings\|\.claude/' scripts/generate_configs.py && ! grep -q 'shutil.which.*claude' scripts/lib/cli_detect.py && echo OK`

---

### Tarefa 3: Remover Referências CC dos Shell Scripts

**Arquivos:**
- Modify: `hooks/_lib/distill.sh` - mudar `.claude/rules/` -> `.kiro/rules/`
- Modify: `hooks/feedback/context-enrichment.sh` - mudar `RULES_DIR=".claude/rules"` -> `.kiro/rules`
- Modify: `tools/validate-project.sh` - remover validações de CC
- Modify: `tools/install-skill.sh` - remover paths de registro de skill CC
- Modify: `tests/test-validate-project.sh` - remover assertions específicas de CC
- Modify: `tests/test-install-skill.sh` - remover assertions específicas de CC

**O que implementar:**
Atualizar todos os shell scripts ativos que referenciam paths `.claude/`. Hooks que verificam `.claude/rules/` passam a usar apenas `.kiro/rules/`.

**Verificação:** `! grep -q '.claude/rules' hooks/_lib/distill.sh hooks/feedback/context-enrichment.sh && echo OK`

---

### Tarefa 4: Renomear OMCC -> OMK

**Arquivos:**
- Rename: `.omcc-overlay.json` -> `.omk-overlay.json`
- Rename: `tools/sync-omcc.sh` -> `tools/sync-omk.sh`
- Modify: `tools/sync-omk.sh` - atualizar OMCC->OMK, remover lógica de submodule CC
- Modify: `tools/init-project.sh` - atualizar OMCC->OMK
- Modify: `tools/validate-project.sh` - atualizar OMCC->OMK
- Modify: `scripts/generate_configs.py` - atualizar OMCC->OMK (nome do arquivo de overlay, comentários)
- Modify: `tests/sync-omcc/test_mcp_sync.sh` - atualizar referências
- Modify: `tests/test-init-project.sh` - atualizar referências
- Modify: `tests/test-validate-project.sh` - atualizar referências
- Modify: `tests/test-agents-template.sh` - atualizar referências

**O que implementar:**
Renomear a marca OMCC para OMK em todas as ferramentas ativas. Config de overlay `.omcc-overlay.json` -> `.omk-overlay.json`. Tool de sync -> `sync-omk.sh`.

**Verificação:** `test -f .omk-overlay.json && test -f tools/sync-omk.sh && test ! -f .omcc-overlay.json && test ! -f tools/sync-omcc.sh && echo OK`

---

### Tarefa 5: Backward Compatibility para Projetos Downstream

**Arquivos:**
- Modify: `tools/sync-omk.sh` - fallback: se `.omk-overlay.json` não for encontrado, tentar `.omcc-overlay.json` com warning de deprecation
- Modify: `scripts/generate_configs.py` - mesmo fallback para detecção de overlay
- Modify: `tools/validate-project.sh` - aceitar ambos os nomes de arquivo de overlay

**O que implementar:**
O GTM tem `.omcc-overlay.json` e `.gitmodules` apontando para o submodule `.omcc`. A tool de sync detecta o nome antigo e imprime um warning de deprecation. Isso dá uma janela de migração para projetos downstream.

**Verificação:** `grep -q 'omcc-overlay' tools/sync-omk.sh && grep -q 'omcc-overlay' scripts/generate_configs.py && grep -q 'deprecated\|DEPRECATED\|deprecat' tools/sync-omk.sh && echo OK`

---

### Tarefa 6: Atualizar Documentação

**Arquivos:**
- Modify: `README.md` - renomear o projeto, remover "Claude Code" de "Works with", atualizar OMCC->OMK
- Modify: `AGENTS.md` - atualizar identidade de OMCC para OMK, remover referência a `.claude/rules/`
- Modify: `knowledge/INDEX.md` - remover entrada de pesquisa CC, atualizar referências OMCC
- Modify: `docs/EXTENSION-GUIDE.md` - atualizar OMCC->OMK
- Modify: `templates/agents-sections/` - atualizar referências OMCC
- Modify: `templates/agents-types/gtm.md` - atualizar referências OMCC, se houver

**O que implementar:**
Atualizar toda a documentação ativa. Docs históricos em `archive/` e `docs/plans/` ficam inalterados.

**Verificação:** `head -1 README.md | grep -q 'oh-my-kiro' && grep -q 'OMK\|oh-my-kiro' AGENTS.md && echo OK`

---

### Tarefa 7: Atualizar Config e Regras do Kiro

**Arquivos:**
- Modify: `.kiro/rules/enforcement.md` - remover entradas de hook específicas de CC
- Modify: `.kiro/rules/commands.md` - atualizar referências OMCC, se houver
- Modify: `.kiro/settings/mcp.json` - atualizar se referenciar OMCC

**O que implementar:**
Garantir que arquivos de config em `.kiro/` estejam consistentes com a marca OMK e não referenciem o Claude Code.

**Verificação:** `! grep -q 'claude\|omcc\|OMCC' .kiro/rules/enforcement.md .kiro/rules/commands.md .kiro/settings/mcp.json 2>/dev/null && echo OK`

---

### Tarefa 8: Script de Migração Downstream

**Arquivos:**
- Create: `tools/migrate-omcc-to-omk.sh`

**O que implementar:**
Um script de migração one-shot para projetos downstream (GTM etc.) que usam OMCC como submodule. O script:
1. Detecta `.omcc-overlay.json` -> renomeia para `.omk-overlay.json`
2. Remove o diretório `.claude/` e `CLAUDE.md` se presentes
3. Executa `sync-omk.sh` para regenerar configs
4. Imprime um resumo do que foi alterado

Uso: `cd /path/to/downstream-project && .omcc/tools/migrate-omcc-to-omk.sh`

NÃO renomeia o path do submodule `.omcc` em `.gitmodules` - isso é uma operação git separada que o usuário pode fazer depois.

**Verificação:** `bash -n tools/migrate-omcc-to-omk.sh && head -1 tools/migrate-omcc-to-omk.sh | grep -q bash && echo OK`

---

### Tarefa 9: Renomear o Repositório no GitHub

**O que implementar:**
Usar `gh api` para renomear o repo no GitHub de `oh-my-claude-code` para `oh-my-kiro`. Atualizar a URL do remote git local para corresponder. O GitHub cria um redirect automaticamente a partir do nome antigo.

**Verificação:** `gh repo view KaimingWan/oh-my-kiro --json name -q .name 2>/dev/null | grep -q oh-my-kiro && echo OK`

---

### Tarefa 10: Validação Final

**O que implementar:**
Rodar a suíte de testes completa. Fazer grep de referências remanescentes a `claude` e `omcc` no código ativo (excluindo archive/ e docs/plans/) para capturar pontos esquecidos.

**Verificação:** `! grep -rl 'claude\|omcc\|OMCC' --include='*.sh' --include='*.py' hooks/ scripts/ tools/ .kiro/ skills/ commands/ templates/ 2>/dev/null | grep -v __pycache__ && echo CLEAN`

## Review

**Round 1 (4 reviewers: Goal Alignment + Verify Correctness + Completeness + Security/Compatibility):**

- Goal Alignment: APPROVE - todas as 8 tarefas mapeiam para frases do objetivo, ordem de execução correta
- Verify Correctness: REQUEST CHANGES - alegou falso positivo do `&& echo OK` da Tarefa 1 (rejeitado: o `&&` do shell faz short-circuit corretamente), pediu teste funcional de fallback para a Tarefa 5 (aceito: verify reforçado)
- Completeness: REQUEST CHANGES - alegou que falta compat de overlay em generate_configs.py (rejeitado: já está na lista de Arquivos da Tarefa 5), alegou quebra de fallback em cli_detect.py (rejeitado: remover claude É o objetivo)
- Security/Compatibility: REQUEST CHANGES - alegou lógica invertida do verify da Tarefa 2 (rejeitado: `! grep -q` está correto), notou pressuposto de symlink (risco baixo, confirmado na Phase 0)

**Resolução:** Verify da Tarefa 5 reforçado para também checar a presença da string de warning de deprecation. Outras descobertas rejeitadas com a justificativa acima.

## Checklist

- [ ] diretório .claude/ removido | `test ! -d .claude && echo OK`
- [ ] CLAUDE.md removido | `test ! -f CLAUDE.md && echo OK`
- [ ] testes de integração CC removidos | `test ! -d tests/cc-integration && echo OK`
- [ ] teste de compat CC removido | `test ! -f tests/hooks/test-cc-compat.sh && echo OK`
- [ ] docs de pesquisa CC removidos | `test ! -f knowledge/claude-code-research.md && test ! -f docs/claude-code-gap-analysis.md && echo OK`
- [ ] generate_configs.py sem funções CC | `! grep -q 'def cc_\|def claude_settings\|\.claude/' scripts/generate_configs.py`
- [ ] cli_detect.py sem detecção de claude | `! grep -q "which.*claude\|shutil.which.*claude" scripts/lib/cli_detect.py`
- [ ] distill.sh usa .kiro/rules | `grep -q '.kiro/rules' hooks/_lib/distill.sh && ! grep -q '\.claude/rules' hooks/_lib/distill.sh`
- [ ] context-enrichment.sh usa .kiro/rules | `grep -q '.kiro/rules' hooks/feedback/context-enrichment.sh && ! grep -q '.claude/rules' hooks/feedback/context-enrichment.sh`
- [ ] arquivo de overlay renomeado | `test -f .omk-overlay.json && test ! -f .omcc-overlay.json`
- [ ] tool de sync renomeada | `test -f tools/sync-omk.sh && test ! -f tools/sync-omcc.sh`
- [ ] tool de sync tem backward compat | `grep -q 'omcc-overlay' tools/sync-omk.sh`
- [ ] generate_configs tem backward compat | `grep -q 'omcc-overlay' scripts/generate_configs.py`
- [ ] README diz oh-my-kiro | `head -1 README.md | grep -q 'oh-my-kiro'`
- [ ] README sem "Claude Code" em Works with | `! grep -q 'Works with.*Claude Code' README.md`
- [ ] AGENTS.md diz OMK | `grep -q 'OMK\|oh-my-kiro' AGENTS.md && ! grep -q 'OMCC\|oh-my-claude-code' AGENTS.md`
- [ ] sem claude/omcc em código ativo (excl archive+plans) | `! grep -rl 'claude\|omcc\|OMCC' --include='*.sh' --include='*.py' hooks/ scripts/ tools/ .kiro/ skills/ commands/ templates/ 2>/dev/null | grep -v __pycache__`
- [ ] sem claude/omcc em docs ativos (excl archive+plans) | `! grep -rl 'claude\|OMCC\|omcc' README.md AGENTS.md knowledge/INDEX.md knowledge/rules.md docs/EXTENSION-GUIDE.md 2>/dev/null`
- [ ] script de migração existe e é válido | `bash -n tools/migrate-omcc-to-omk.sh && grep -q 'omcc-overlay' tools/migrate-omcc-to-omk.sh && grep -q 'sync-omk' tools/migrate-omcc-to-omk.sh`
- [ ] repo no GitHub renomeado | `gh repo view KaimingWan/oh-my-kiro --json name -q .name 2>/dev/null | grep -q oh-my-kiro`
- [ ] testes Python passando | `python3 -m pytest tests/test_generate_configs.py tests/ralph-loop/test_ralph_loop.py tests/test_debugging_rules.py -v 2>&1 | tail -5`
- [ ] sintaxe shell válida para hooks modificados | `bash -n hooks/_lib/distill.sh && bash -n hooks/feedback/context-enrichment.sh && echo OK`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Descobertas
