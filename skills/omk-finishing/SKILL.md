---
name: omk-finishing
description: "Branch completion workflow: verify tests → present 4 options (merge/PR/keep/discard) → execute → cleanup worktree. Trigger when implementation is complete, all tests pass, user says 'done', 'finish', 'merge', 'create PR', 'push', 'wrap up', '@cpu', or when ready to integrate work back to main branch."
---

## Trigger Examples
- "代码写完了，帮我合并"
- "push and create a PR"
- "这个分支可以收了"
- "wrap up this feature branch"
- "discard this work, start over"

# Finalizando uma branch de desenvolvimento

## Visão geral

Conduza a conclusão do trabalho apresentando opções claras e tratando o workflow escolhido.

**Princípio central:** Verificar testes → apresentar opções → executar a escolha → limpar.

**Anuncie no início:** "I'm using the finishing-a-development-branch skill to complete this work."

## O processo

### Step 1: Verificar testes

**Antes de apresentar opções, verifique se os testes passam:**

```bash
# Run project's test suite
npm test / cargo test / pytest / go test ./...
```

**Se os testes falharem:**
```
Tests failing (<N> failures). Must fix before completing:

[Show failures]

Cannot proceed with merge/PR until tests pass.
```

Pare. Não prossiga para o Step 2.

**Se os testes passarem:** continue para o Step 2.

### Step 2: Determinar a base branch

```bash
# Try common base branches
git merge-base HEAD main 2>/dev/null || git merge-base HEAD master 2>/dev/null
```

Ou pergunte: "This branch split from main - is that correct?"

### Step 3: Apresentar opções

Apresente exatamente estas 4 opções:

```
Implementation complete. What would you like to do?

1. Merge back to <base-branch> locally
2. Push and create a Pull Request
3. Keep the branch as-is (I'll handle it later)
4. Discard this work

Which option?
```

**Não adicione explicação**, mantenha as opções concisas.

### Step 4: Executar a escolha

#### Opção 1: Merge local

```bash
# Switch to base branch
git checkout <base-branch>

# Pull latest
git pull

# Merge feature branch
git merge <feature-branch>

# Verify tests on merged result
<test command>

# If tests pass
git branch -d <feature-branch>
```

Em seguida: limpeza do worktree (Step 5)

#### Opção 2: Push e criar PR

```bash
# Push branch
git push -u origin <feature-branch>

# Create PR
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<2-3 bullets of what changed>

## Test Plan
- [ ] <verification steps>
EOF
)"
```

Em seguida: limpeza do worktree (Step 5)

#### Opção 3: Manter como está

Reporte: "Keeping branch <name>. Worktree preserved at <path>."

**Não limpe o worktree.**

#### Opção 4: Descartar

**Confirme primeiro:**
```
This will permanently delete:
- Branch <name>
- All commits: <commit-list>
- Worktree at <path>

Type 'discard' to confirm.
```

Aguarde a confirmação exata.

Se confirmado:
```bash
git checkout <base-branch>
git branch -D <feature-branch>
```

Em seguida: limpeza do worktree (Step 5)

### Step 5: Limpeza do worktree

**Para as opções 1, 2 e 4:**

Verifique se está em worktree:
```bash
git worktree list | grep $(git branch --show-current)
```

Se sim:
```bash
git worktree remove <worktree-path>
```

**Para a opção 3:** mantenha o worktree.

## Referência rápida

| Opção | Merge | Push | Manter Worktree | Limpar branch |
|--------|-------|------|---------------|----------------|
| 1. Merge local | ✓ | - | - | ✓ |
| 2. Criar PR | - | ✓ | ✓ | - |
| 3. Manter como está | - | - | ✓ | - |
| 4. Descartar | - | - | - | ✓ (force) |

## Erros comuns

**Pular a verificação de testes**
- **Problema:** Mergear código quebrado, criar PR com falhas
- **Fix:** Sempre verifique os testes antes de oferecer opções

**Perguntas abertas**
- **Problema:** "What should I do next?" → ambíguo
- **Fix:** Apresente exatamente 4 opções estruturadas

**Limpeza automática do worktree**
- **Problema:** Remover worktree quando ele ainda pode ser necessário (Opção 2, 3)
- **Fix:** Faça cleanup apenas para as opções 1 e 4

**Sem confirmação para discard**
- **Problema:** Apagar trabalho por acidente
- **Fix:** Exija confirmação digitada "discard"

## Sinais de alerta

**Nunca:**
- Prosseguir com testes falhando
- Mergear sem verificar os testes no resultado
- Apagar trabalho sem confirmação
- Force-push sem solicitação explícita

**Sempre:**
- Verifique os testes antes de oferecer opções
- Apresente exatamente 4 opções
- Exija confirmação digitada para a Opção 4
- Limpe o worktree apenas para as Opções 1 e 4

## Integração

**Chamado por:**
- **subagent-driven-development** (Step 7), depois que todas as tasks são concluídas
- **executing-plans** (Step 5), depois que todos os batches são concluídos

**Combina com:**
- **using-git-worktrees**, limpa o worktree criado por essa skill
