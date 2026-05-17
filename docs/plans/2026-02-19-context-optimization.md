# Plano de Otimização de Contexto e Skill

**Objetivo:** Reduce context overhead by ~40% (skill resources) and ~500-800 bytes/message (hook output), while maintaining full CC + Kiro capability parity. Eliminate skill redundancy, streamline hook verbosity, and trigger episodes distillation.

**Não-Objetivos:**
- Rewriting hook logic or changing enforcement behavior
- Modifying planning/reviewing skill content (beyond brainstorming merge)
- Changing the knowledge retrieval architecture (INDEX.md stays)
- Restructuring the hook system itself

**Arquitetura:** Three-layer optimization: (1) resource loading - reduce from 9 skills to 2 preloaded, (2) hook output - strip internal diagnostics, keep only actionable messages, (3) episodes cleanup - trigger distillation to unblock the pipeline. All changes flow through generate_configs.py as single source of truth.

**Tech Stack:** Bash (hooks), Python (generate_configs.py), Markdown (skills, plans, AGENTS.md)

## Tarefas

### Tarefa 1: Skill Resource Pruning in generate_configs.py

**Arquivos:**
- Modify: `scripts/generate_configs.py`

Change pilot/default resources from `skill://skills/**/SKILL.md` (all 9 skills) to explicit `skill://skills/planning/SKILL.md` + `skill://skills/reviewing/SKILL.md` (2 skills). Remove `AGENTS.md` from reviewer and researcher subagent resources (they don't need full framework principles).

**Verificação:**
```bash
python3 scripts/generate_configs.py && jq '.resources' .kiro/agents/pilot.json | grep -c 'skill://' | grep -q '^2$' && echo PASS || echo FAIL
```

### Tarefa 2: Merge Brainstorming into Planning Phase 0

**Arquivos:**
- Modify: `skills/planning/SKILL.md`
- Modify: `commands/plan.md`
- Move: `skills/brainstorming/` → `.trash/brainstorming/`

Add brainstorming's unique value (design presentation in 200-300 word sections, write to docs/designs/) to planning Phase 0 as optional step. Update commands/plan.md Step 1 to reference planning Phase 0 instead of brainstorming.

**Verificação:**
```bash
test ! -d skills/brainstorming && grep -q 'Design presentation' skills/planning/SKILL.md && ! grep -q 'brainstorming' commands/plan.md && echo PASS || echo FAIL
```

### Tarefa 3: Update AGENTS.md Skill Routing Table

**Arquivos:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`

Update Skill Routing table to reflect new loading strategy (preloaded vs on-demand). Sync CLAUDE.md = AGENTS.md.

**Verificação:**
```bash
grep -q '加载方式' AGENTS.md && diff AGENTS.md CLAUDE.md > /dev/null && echo PASS || echo FAIL
```

### Tarefa 4: Hook Output Streamlining - context-enrichment.sh

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`
- Modify: `tests/knowledge/test-enrichment-v2.sh`

Layer 3 (episode hints): change from outputting each episode's 40-char summary (N lines) to single count line `📌 N related episodes found`. Layer 4 (archive hint): remove entirely. Update test assertions (including E5 archive assertion removal in test-enrichment-v2.sh).

**Verificação:**
```bash
bash tests/knowledge/test-enrichment-v2.sh
```

### Tarefa 5: Hook Output Streamlining - Other Hooks

**Arquivos:**
- Modify: `hooks/feedback/session-init.sh`
- Modify: `hooks/feedback/auto-capture.sh`
- Modify: `hooks/feedback/verify-completion.sh`
- Modify: `hooks/feedback/post-write.sh`
- Modify: `hooks/_lib/distill.sh`
- Modify: `hooks/gate/enforce-ralph-loop.sh`
- Modify: `tests/knowledge/test-distill.sh`
- Modify: `tests/hooks/test-auto-capture.sh`

session-init: remove 🧹 cleanup and 📊 health report output, keep ⬆️ promotion reminder. auto-capture: remove "Already in rules" and "Similar episode exists" dedup diagnostics. verify-completion: remove ═══ decoration lines, compact INCOMPLETE to 1 line. post-write: remove "File updated" reminder. distill.sh: silence "Distilled" and "Archived" output. enforce-ralph-loop: compact block_msg function to output 1 echo line instead of 4. Update affected test assertions (including test-enrichment-v2.sh E5 archive assertion, test-severity-tracking.sh capacity assertion).

**Verificação:**
```bash
bash tests/knowledge/test-distill.sh && bash tests/hooks/test-auto-capture.sh && bash tests/knowledge/test-integration.sh && bash tests/knowledge/test-severity-tracking.sh && echo PASS || echo FAIL
```

### Tarefa 6: Trigger Episodes Distillation

**Arquivos:**
- Modify: `knowledge/episodes.md`
- Modify: `knowledge/rules.md`

Run distill pipeline to promote high-frequency keywords (≥2 occurrences) to rules.md, archive promoted episodes, enforce section cap. Target: active episodes ≤ 30.

**Verificação:**
```bash
test $(grep -c '| active |' knowledge/episodes.md) -le 30 && grep -c '^## \[' knowledge/rules.md | grep -qv '^0$' && echo PASS || echo FAIL
```

### Tarefa 7: Regenerate Configs & Final Validation

**Arquivos:**
- Modify: `.kiro/agents/default.json` (generated)
- Modify: `.kiro/agents/pilot.json` (generated)
- Modify: `.kiro/agents/reviewer.json` (generated)
- Modify: `.kiro/agents/researcher.json` (generated)
- Modify: `.claude/settings.json` (generated)
- Modify: `.claude/agents/reviewer.md` (generated)
- Modify: `.claude/agents/executor.md` (generated)
- Modify: `.claude/agents/researcher.md` (generated)

Regenerate all configs from generate_configs.py, validate, run full test suite.

**Verificação:**
```bash
python3 scripts/generate_configs.py --validate && bash tests/knowledge/test-enrichment-v2.sh && bash tests/knowledge/test-distill.sh && echo PASS || echo FAIL
```

## Review

Round 1: Goal Alignment REQUEST CHANGES, Verify Correctness REQUEST CHANGES, Completeness REQUEST CHANGES, Technical Feasibility APPROVE. Fixed: checklist item 14 grep→awk, Task 4/5 explicit test updates, added test-severity-tracking.
Round 2: Goal Alignment APPROVE, Verify Correctness false positive (confused current vs target state).
Verdict: APPROVE

## Checklist

- [x] resources de generate_configs.py carrega apenas planning + reviewing | `python3 scripts/generate_configs.py && jq '.resources' .kiro/agents/pilot.json | grep -c 'skill://' | grep -q '^2$'`
- [x] subagent nao carrega mais AGENTS.md | `python3 scripts/generate_configs.py && ! jq '.resources[]' .kiro/agents/reviewer.json 2>/dev/null | grep -q 'AGENTS.md'`
- [x] brainstorming fundido na planning Phase 0 e removido | `test ! -d skills/brainstorming && grep -q 'Design presentation' skills/planning/SKILL.md`
- [x] commands/plan.md nao referencia mais brainstorming | `! grep -q 'brainstorming' commands/plan.md`
- [x] tabela Skill Routing de AGENTS.md atualizada | `grep -q '加载方式' AGENTS.md`
- [x] CLAUDE.md sincronizado com AGENTS.md | `diff AGENTS.md CLAUDE.md`
- [x] context-enrichment hints de episode reduzidos a contagem | `echo '{"prompt":"test subagent code"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '📌' && ! echo '{"prompt":"test subagent code"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q 'Episode:'`
- [x] hint de archive removido | `! echo '{"prompt":"test"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '📦'`
- [x] session-init removeu saida de cleanup/health | `! grep -q '🧹\|📊' hooks/feedback/session-init.sh`
- [x] auto-capture removeu saida diagnostica de dedup | `! grep -q 'Already in rules\|Similar episode exists' hooks/feedback/auto-capture.sh`
- [x] verify-completion removeu linhas decorativas | `! grep -q '═══' hooks/feedback/verify-completion.sh`
- [x] post-write removeu lembretes de baixo valor | `! grep -q 'File updated' hooks/feedback/post-write.sh`
- [x] distill.sh executa em modo silencioso | `! grep -qE 'echo.*Distilled|echo.*Archived' hooks/_lib/distill.sh`
- [x] funcao block_msg de enforce-ralph-loop reduzida a 1 linha de output | `awk '/^block_msg/,/^}/' hooks/gate/enforce-ralph-loop.sh | grep -c 'echo' | grep -q '^1$'`
- [x] destilacao de episodes concluida (active <= 30) | `test $(grep -c '| active |' knowledge/episodes.md) -le 30`
- [x] rules.md possui saida da destilacao | `grep -c '^## \[' knowledge/rules.md | grep -qv '^0$'`
- [x] testes passam: enrichment | `bash tests/knowledge/test-enrichment-v2.sh`
- [x] testes passam: distill | `bash tests/knowledge/test-distill.sh`
- [x] testes passam: integration | `bash tests/knowledge/test-integration.sh`
- [x] testes passam: auto-capture | `bash tests/hooks/test-auto-capture.sh`
- [x] testes passam: severity-tracking | `bash tests/knowledge/test-severity-tracking.sh`
- [x] validacao de geracao de configs passa | `python3 scripts/generate_configs.py --validate`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
