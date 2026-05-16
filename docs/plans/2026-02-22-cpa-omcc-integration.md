> **Status:** draft

# Plano de Integração CPA OMCC

**Objetivo:** Integrate OMCC framework into china-poetry-app (CPA) via git submodule, inheriting all framework capabilities (hooks, skills, principles, workflow, self-learning) while preserving CPA's MoXun Identity/Roles and project-specific knowledge/skills/hooks. Also complete OMCC's own Identity/Roles definition (dogfooding).

**Não-Objetivos:**
- Modifying CPA business code (moxun/, worker/, audio/)
- Changing CPA's knowledge content (16 domain files)
- Adding new framework features — only using existing extension points
- Ralph loop cross-project support (separate plan)

**Arquitetura:** CPA adds OMCC as git submodule at `.omcc/`. Top-level `hooks/` and `skills/` directories use sub-directory symlinks to framework content + real directories for project-specific content. `.omcc-overlay.json` registers project hooks/skills. `sync-omcc.sh` regenerates all agent configs. AGENTS.md uses `<!-- BEGIN/END OMCC -->` markers for framework section inheritance.

**Tech Stack:** Bash (integration scripts), Python (generate_configs.py), JSON (overlay/agent configs)

## Contexto

### CPA Current State
- AGENTS.md: MoXun Agent v2 format (~80 lines), Identity + 3 Roles (Engineer/iOS QA/Design) + Workflow
- CLAUDE.md: template placeholder `[Project Name]`, not customized
- `.kiro/hooks/`: 5 scripts (deny-commands, enforce-research, enforce-code-quality, three-rules-check, check-persist)
- `.kiro/skills/`: 30 skills (22 old Kiro built-in + 8 project-specific)
- `.agents/skills/`: 8 project-specific skills (code-review-expert, ios-simulator-skill, ios-testing-patterns, maestro-mobile-testing, mobile-design, mobile-ios-design, ui-ux-pro-max, xcodebuildmcp-cli)
- `.claude/skills/`: 7 project-specific skills (subset of .agents/skills/)
- `.claude/settings.json`: permissions only, no hooks
- `knowledge/`: 16 domain files with INDEX.md
- `.kiro/rules/`: enforcement.md, reference.md, commands.md (project-specific)

### CPA Hooks to Preserve
- `enforce-code-quality.sh` → move to `hooks/project/`
- `deny-commands.sh`, `enforce-research.sh`, `three-rules-check.sh`, `check-persist.sh` → superseded by OMCC hooks (block-dangerous, context-enrichment, verify-completion, etc.)

### CPA Project-Specific Skills (8)
- code-review-expert, ios-simulator-skill, ios-testing-patterns, maestro-mobile-testing
- mobile-design, mobile-ios-design, ui-ux-pro-max, xcodebuildmcp-cli

### OMCC Current State
- AGENTS.md Identity: generic "Agent for this project" — needs proper definition
- All extension point tools ready: init-project.sh, sync-omcc.sh, validate-project.sh, install-skill.sh, generate_configs.py with overlay support

## Decisões de Design

1. **OMCC Identity/Roles** — Define as framework development agent (architect + devops + quality guardian), not generic "coding agent"
2. **CPA hooks migration** — Only `enforce-code-quality.sh` preserved; other 4 are functionally superseded by OMCC's layered hook system
3. **CPA skills migration** — 22 old Kiro built-in skills removed (superseded by OMCC's 8 framework skills); 8 project-specific skills moved to top-level `skills/`
4. **AGENTS.md upgrade** — Preserve MoXun Identity/Roles/Knowledge sections, wrap framework sections with BEGIN/END markers
5. **CLAUDE.md** — Generate from AGENTS.md (same content, CC compatibility)
6. **CPA `.kiro/rules/`** — Preserved as-is (project-specific enforcement rules), OMCC rules added via `.claude/rules → .omcc/.claude/rules` symlink

## Tarefas

### Tarefa 1: [OMCC] Complete OMCC's own Identity and Roles

**Arquivos:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `templates/agents-types/coding.md`

**Do:**
- Update OMCC's AGENTS.md Identity from generic "Agent for this project" to:
  ```
  ## Identity
  - OMCC (oh-my-claude-code) 框架开发 agent。中英双语，跟随用户语言。
  ```
- Add Roles section after Identity:
  ```
  ## Roles
  - Agent framework architect — hooks、skills、config 生成、扩展点体系设计
  - DevOps engineer — bash/python 脚本、跨平台兼容（macOS/Linux）、CI
  - Quality guardian — TDD、hook enforcement、安全审计、code review
  ```
- Sync same changes to CLAUDE.md
- Update `templates/agents-types/coding.md` to have more descriptive default Roles (current ones are fine, just ensure consistency)

**Verificação:** `grep -q 'OMCC.*框架开发' AGENTS.md && grep -q 'framework architect' AGENTS.md`

### Tarefa 2: [CPA] Write integration script

**Arquivos:**
- Create: `tools/integrate-cpa.sh`

**Do:**
Create a self-contained bash script that performs the full CPA integration when run from the CPA directory. The script:

1. Adds OMCC as git submodule at `.omcc/`
2. Creates top-level `hooks/` with sub-directory symlinks:
   - `hooks/security → ../.omcc/hooks/security/`
   - `hooks/gate → ../.omcc/hooks/gate/`
   - `hooks/feedback → ../.omcc/hooks/feedback/`
   - `hooks/_lib → ../.omcc/hooks/_lib/`
   - `hooks/project/` — real directory, moves `enforce-code-quality.sh` here
   - Copies dispatcher scripts: `hooks/dispatch-*.sh` from `.omcc/hooks/`
3. Creates top-level `skills/` with symlinks to OMCC framework skills + moves 8 project-specific skills from `.agents/skills/`
4. Creates `.omcc-overlay.json` registering project hook and skills
5. Symlinks: `.kiro/hooks → ../hooks`, `.claude/hooks → ../hooks`, `.kiro/skills → ../skills`, `.claude/skills → ../skills`
6. Adds `.claude/rules → .omcc/.claude/rules` symlink for framework rules
7. Preserves `.kiro/rules/` (project-specific), `.kiro/settings/`, `knowledge/`
8. Generates new AGENTS.md (v3 format with MoXun Identity preserved + BEGIN/END OMCC markers)
9. Generates CLAUDE.md from AGENTS.md
10. Runs `sync-omcc.sh` to generate all agent configs
11. Cleans up old artifacts (`.agents/`, old `.kiro/hooks/` scripts, old `.kiro/skills/` built-in skills)

Script must be idempotent (safe to re-run) and create a backup branch before changes.

**Verificação:** `bash -n tools/integrate-cpa.sh`

### Tarefa 3: [CPA] Write CPA's v3 AGENTS.md template

**Arquivos:**
- Create: `tools/cpa-agents-template.md`

**Do:**
Write the complete AGENTS.md content for CPA in v3 format:

```markdown
# MoXun Agent

## Identity
- MoXun Agent — 墨寻产品的全栈工程师
- 中文优先（用户使用中文时），English for code/comments

## Roles

| Role | Trigger | Knowledge Source |
|------|---------|-----------------|
| 🔧 Engineer | Technical tasks | `knowledge/` |
| 📱 iOS QA | UI 布局/CLS/测试/截图/分享卡片 | `knowledge/ios-testing-skills.md` → activate `ios-simulator-skill` + `xcodebuildmcp-cli` |
| 🎨 Design | 审美/排版/间距/色彩/动画 | `knowledge/ios-aesthetic-design.md` → activate `mobile-ios-design` |

## Domain Rules
- Expo/React Native 技术栈，iOS 优先
- 设计变更必须同步 PRD + design spec
- UI 修改必须截图验证

<!-- BEGIN OMCC PRINCIPLES -->
<!-- END OMCC PRINCIPLES -->

<!-- BEGIN OMCC WORKFLOW -->
<!-- END OMCC WORKFLOW -->

## Project Skill Routing

| 场景 | Skill | 触发方式 |
|------|-------|---------|
| iOS 模拟器操作 | ios-simulator-skill | iOS QA role |
| Xcode 构建 | xcodebuildmcp-cli | iOS QA role |
| 移动端设计 | mobile-design / mobile-ios-design | Design role |
| UI/UX 审查 | ui-ux-pro-max | Design role |
| iOS 测试模式 | ios-testing-patterns | iOS QA role |
| Maestro 测试 | maestro-mobile-testing | iOS QA role |
| Code Review | code-review-expert | @review |

## Knowledge Retrieval
- Question → knowledge/INDEX.md → topic indexes → source docs
- Must cite source files

<!-- BEGIN OMCC SELF-LEARNING -->
<!-- END OMCC SELF-LEARNING -->

<!-- BEGIN OMCC AUTHORITY -->
<!-- END OMCC AUTHORITY -->
```

The integration script (Task 2) will use this template and fill in the OMCC sections via `sync-omcc.sh`.

**Verificação:** `test -f tools/cpa-agents-template.md && grep -q 'MoXun Agent' tools/cpa-agents-template.md && grep -q 'BEGIN OMCC PRINCIPLES' tools/cpa-agents-template.md`

### Tarefa 4: [OMCC] Verify integration script with dry-run

**Arquivos:**
- Test: `tools/integrate-cpa.sh`

**Do:**
- Run the integration script with `--dry-run` flag (script should support this) to verify all paths and operations without making changes
- Verify script syntax: `bash -n tools/integrate-cpa.sh`
- Verify all referenced OMCC paths exist (hooks, skills, templates, tools)

**Verificação:** `bash -n tools/integrate-cpa.sh && bash tools/integrate-cpa.sh --dry-run /tmp/test-cpa-integration 2>&1 | grep -q 'dry-run complete'`

## CPA Integration Guide

After Tasks 1-4 are complete in OMCC, run these commands in the CPA directory:

```bash
# 1. Go to CPA directory
cd /Users/wanshao/project/china-poetry-app

# 2. Create backup branch
git checkout -b backup/pre-omcc-integration
git checkout -

# 3. Run integration script from OMCC
bash /Users/wanshao/project/oh-my-claude-code/tools/integrate-cpa.sh .

# 4. Verify (runs after sync, which already happened in step 3)
bash .omcc/tools/validate-project.sh .

# 5. Smoke test: configs are valid JSON
python3 -c "import json; json.load(open('.kiro/agents/default.json'))"
python3 -c "import json; json.load(open('.claude/settings.json'))"

# 6. Verify MoXun identity preserved
grep -q 'MoXun Agent' AGENTS.md

# 7. Verify framework hooks present
jq '.hooks.preToolUse[] | select(.command | contains("block-dangerous"))' .kiro/agents/default.json

# 8. Verify project hook present
jq '.hooks.preToolUse[] | select(.command | contains("enforce-code-quality"))' .kiro/agents/default.json

# 9. Verify knowledge untouched
git diff --stat -- knowledge/

# 10. Verify no business code changes
git diff --stat -- moxun/ worker/

# 11. Commit
git add -A && git commit -m "feat: integrate OMCC framework via submodule"
```

### Future Sync

```bash
cd /Users/wanshao/project/china-poetry-app
bash .omcc/tools/sync-omcc.sh .
git add -A && git commit -m "chore: sync OMCC to $(cd .omcc && git rev-parse --short HEAD)"
```

## Review

### Round 1 (4 reviewers, 2026-02-22)

**Findings addressed:**
- ✅ Task 2→3 dependency: clarified template location (co-located at tools/cpa-agents-template.md)
- ✅ Checklist #2: replaced grep-based diff with head-based diff for accurate Identity comparison
- ✅ Validation timing: sync-omcc.sh runs before validate-project.sh in integration script
- ✅ Idempotency: added explicit idempotency requirements + checklist item for re-run verification
- ✅ Error paths: added error handling requirements to Task 2

## Checklist

- [ ] OMCC AGENTS.md has proper Identity and Roles | `grep -q 'OMCC.*框架开发' AGENTS.md && grep -q 'framework architect' AGENTS.md`
- [ ] OMCC CLAUDE.md matches AGENTS.md Identity | `head -5 AGENTS.md | diff - <(head -5 CLAUDE.md)`
- [ ] integrate-cpa.sh syntax valid | `bash -n tools/integrate-cpa.sh`
- [ ] integrate-cpa.sh dry-run passes | `bash tools/integrate-cpa.sh --dry-run /tmp/test-cpa-integration 2>&1 | grep -q 'dry-run complete'`
- [ ] CPA AGENTS.md template has MoXun Identity | `grep -q 'MoXun Agent' tools/cpa-agents-template.md`
- [ ] CPA AGENTS.md template has BEGIN/END OMCC markers | `grep -c 'BEGIN OMCC' tools/cpa-agents-template.md | grep -q '[4-6]'`
- [ ] CPA AGENTS.md template has project skill routing | `grep -q 'ios-simulator-skill' tools/cpa-agents-template.md`
- [ ] Integration script handles existing submodule | `bash tools/integrate-cpa.sh --dry-run /tmp/test-cpa-idempotent 2>&1 | grep -q 'dry-run complete' && bash tools/integrate-cpa.sh --dry-run /tmp/test-cpa-idempotent 2>&1 | grep -q 'dry-run complete'`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
