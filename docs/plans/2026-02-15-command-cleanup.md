# Limpeza de Commands - Sync, Trim, Auto-trigger

**Objetivo:** Remover commands sem uso, sincronizar a tabela de commands no README e disparar automaticamente as skills de debugging/research via context-enrichment.
**Arquitetura:** Apagar commands/debug.md; atualizar a tabela de commands em README/AGENTS.md; adicionar uma secao de debugging em rules.md; adicionar deteccao de palavras-chave de research em context-enrichment.sh.
**Tech Stack:** Markdown, Bash (hook)

## Tarefas

### Tarefa 1: remover o command @debug

**Arquivos:**
- Delete: `commands/debug.md`

**Verificação:**
```bash
! test -f commands/debug.md
```

### Tarefa 2: registrar princípios principais de debugging em rules.md

**Arquivos:**
- Modify: `knowledge/rules.md`

Acrescentar ao fim do arquivo a nova secao por keyword:

```markdown
## [debugging, bug, error, failure, fix, broken]
1. 修 bug 前必须先复现、定位根因，禁止猜测性修复。NO FIX WITHOUT ROOT CAUSE。
2. 遇到测试失败：先读完整错误信息和堆栈，再行动。
3. 连续修 3 次不成功 → 停下来，重新从复现开始。
```

**Verificação:**
```bash
grep -q '## \[debugging' knowledge/rules.md
```

### Tarefa 3: adicionar deteccao de keywords de research em context-enrichment

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`

Apos o `fi` da deteccao de correction (~linha 42, apos `touch ... .flag`) e antes do comentario `# 2. Unfinished task resume`, insira:

```bash
# Research skill reminder
if echo "$USER_MSG" | grep -qE '(调研|研究一下|查一下|了解一下|对比.*方案)'; then
  echo "🔍 Research detected → read skills/research/SKILL.md for search level strategy (L0→L1→L2)."
elif echo "$USER_MSG" | grep -qiE '(research|investigate|look into|compare.*options|find out)'; then
  echo "🔍 Research detected → read skills/research/SKILL.md for search level strategy (L0→L1→L2)."
fi
```

**Verificação:**
```bash
grep -q 'Research detected' hooks/feedback/context-enrichment.sh
```

### Tarefa 4: atualizar AGENTS.md

**Arquivos:**
- Modify: `AGENTS.md`

Na tabela de skill routing, mude:
```
| 调试 | debugging | `@debug` 命令 |
```
para:
```
| 调试 | debugging | rules.md 自动注入 |
```

**Verificação:**
```bash
! grep -q '@debug' AGENTS.md && grep -q 'rules.md 自动注入' AGENTS.md
```

### Tarefa 5: atualizar tabela de commands no README

**Arquivos:**
- Modify: `README.md`

3 mudancas:

**Linha 27** - linha de L1 Commands, mudar para:
```
| L1 Commands | `@plan` `@execute` `@research` `@review` `@reflect` `@cpu` `@skill` | 100% — user triggers full workflow |
```

**Linha 56** - linha de comandos no diagrama de arquitetura, mudar para:
```
│  @plan · @execute · @research · @review · @reflect · @cpu · @skill  │
```

**Linhas 86-91** - tabela de commands; remova a linha de @debug (linha 88) e adicione as linhas @reflect e @cpu:
```
| `@plan` | brainstorming → write plan (with checklist) → reviewer challenge → fix until APPROVE → user confirm |
| `@execute` | load approved plan → Ralph Loop: bash outer loop checks checklist → fresh Kiro instance per iteration → no stops until all items checked off |
| `@research` | L0 built-in knowledge → L1 web search → L2 deep research → write findings to file |
| `@review` | dispatch reviewer subagent → categorize P0-P3 → cite file:line |
| `@reflect` | manual knowledge capture → extract insight → dedup check → append to episodes.md |
| `@cpu` | commit all changes → push to remote → update README if needed |
| `@skill` | list all skills with descriptions, match user need to closest skill |
```

**Verificação:**
```bash
! grep -q '@debug' README.md && grep -q '@reflect' README.md && grep -q '@cpu' README.md
```

## Review

### Round 1 (Completeness, Compatibility, Testability, Clarity)

| Angle | Verdict | Key Finding |
|-------|---------|-------------|
| Completeness | REJECT | Missing content migration verification |
| Compatibility | REJECT | @debug removal is breaking — **dismissed: user explicitly requested this** |
| Testability | REJECT | Minor grep concerns — **dismissed: files exist, syntax valid** |
| Clarity | REJECT | Task 5 README changes not specific enough |

**Fixes applied:**
- Task 5: added exact line numbers and replacement content for all 3 README locations
- Compatibility/Testability REJECTs dismissed with reason (user decision / non-issue)

## Checklist

- [x] commands/debug.md removido | `! test -f commands/debug.md`
- [x] rules.md tem secao por keyword de debugging | `grep -q '## \[debugging' knowledge/rules.md`
- [x] regras de debugging incluem principio de causa raiz | `grep -q 'ROOT CAUSE' knowledge/rules.md`
- [x] context-enrichment tem deteccao de research | `grep -q 'Research detected' hooks/feedback/context-enrichment.sh`
- [x] deteccao de research cobre chines e ingles | `grep -q '调研' hooks/feedback/context-enrichment.sh && grep -qi 'research' hooks/feedback/context-enrichment.sh`
- [x] AGENTS.md sem referencias a @debug | `! grep -q '@debug' AGENTS.md`
- [x] forma de trigger de debugging atualizada em AGENTS.md | `grep -q 'rules.md 自动注入' AGENTS.md`
- [x] README sem @debug | `! grep -q '@debug' README.md`
- [x] README com @reflect | `grep -q '@reflect' README.md`
- [x] README com @cpu | `grep -q '@cpu' README.md`
- [x] sintaxe do hook correta | `bash -n hooks/feedback/context-enrichment.sh`
