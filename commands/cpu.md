Faz commit de todas as alterações, push para o remote e completa o ciclo de vida da branch. (CPU = Commit Push Update-readme)

## Escopo
Opera apenas no projeto atual (onde o AGENTS.md vive). NUNCA faça cd para outros repositórios nem rode commit/push neles.

## Steps

### Step 0: Atualizar o README (o "U" em CPU)

Antes de commitar, verifique se o README.md precisa ser atualizado com base no que mudou.

1. Execute `git diff --name-only HEAD` (ou `git diff --name-only --cached HEAD` se estiver em stage) para obter os arquivos alterados.

2. Verifique cada categoria contra o README.md:

| Padrão de path alterado | Seção do README a verificar |
|---------------------|------------------------|
| `commands/*.md` (novo arquivo) | Tabela de comandos (linhas `@command`) |
| `skills/*/SKILL.md` (novo arquivo) | Tabela ou lista de skills |
| `hooks/**/*.sh` (novo arquivo) | Seção de hooks ou árvore de diretórios |
| Qualquer novo diretório de topo | Árvore de diretórios no README |

3. Para cada divergência encontrada:
   - Leia o novo arquivo para entender o que ele faz (primeira linha ou campo description)
   - Adicione a entrada faltante na seção apropriada do README
   - Siga exatamente o formato das entradas existentes

4. Se nenhuma atualização do README for necessária, pule silenciosamente. Se houver atualizações, coloque-as em stage junto com o resto.

**Regra:** Apenas ADICIONE entradas para arquivos novos. NÃO reescreva, reformatar ou "melhore" o conteúdo existente do README.

### Step 1: Stage e Commit
1. `git add -A && git status --short`, mostra o que está em stage
2. Pergunte ao usuário pela commit message se nenhuma foi fornecida, ou gere uma a partir do diff
3. `git commit -m "<message>"`
4. `git push`
5. Reporte: hash do commit + resultado do push

### Step 2: Detectar Worktree

Verifique se está atualmente dentro de um worktree git:

```bash
wt_dir=$(git rev-parse --git-common-dir 2>/dev/null)
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ "$wt_dir" != "$git_dir" ]; then
  echo "IN_WORKTREE=true"
  # Get the base branch (the branch of the main working tree)
  base_branch=$(git -C "$wt_dir/.." branch --show-current 2>/dev/null || echo "main")
  echo "BASE_BRANCH=$base_branch"
else
  echo "IN_WORKTREE=false"
fi
```

- Se **não estiver em worktree** → PARE aqui. Concluído (comportamento original).
- Se **estiver em worktree** → continue para o Step 3.

### Step 3: Verificar a proteção da branch

```bash
# Extract owner/repo from remote
remote_url=$(git remote get-url origin)
repo_slug=$(echo "$remote_url" | sed -E 's#.*[:/]([^/]+/[^/.]+)(\.git)?$#\1#')
gh api "repos/${repo_slug}/branches/${base_branch}/protection" 2>&1
```

- **404 (não protegida)** → Step 4A (merge local)
- **200 (protegida)** → Step 4B (criar PR)
- **Erro do gh CLI / sem auth** → fallback para Step 4B (default mais seguro)

### Step 4A: Merge na main (não protegida)

```bash
feature_branch=$(git branch --show-current)
worktree_path=$(pwd)

# Switch to main working tree
cd "$(git rev-parse --git-common-dir)/.."

# Merge
git merge --no-ff "$feature_branch" -m "merge: $feature_branch"
git push

# Cleanup
git worktree remove "$worktree_path" --force
git branch -d "$feature_branch"
```

Reporte: "Merged `<feature_branch>` into `<base_branch>`, pushed, worktree cleaned up."

### Step 4B: Criar PR (protegida)

```bash
feature_branch=$(git branch --show-current)
worktree_path=$(pwd)

# Create PR
gh pr create --title "<generate from commits>" --body "<summary of changes>"

# Cleanup worktree only (code is on remote, worktree no longer needed)
# Do NOT delete local branch - PR hasn't merged yet
cd "$(git rev-parse --git-common-dir)/.."
git worktree remove "$worktree_path" --force
```

Reporte: "PR created: <url>. Worktree cleaned up. Local branch kept until PR merges."

## Casos de borda
- **Alterações não commitadas no main worktree:** Antes do merge (4A), verifique `git -C <main-tree> status --porcelain`. Se estiver sujo, avise o usuário e aborte o merge.
- **Conflito de merge (4A):** Se `git merge` falhar, aborte com `git merge --abort` e faça fallback para o Step 4B (criar PR).
- **Sem gh CLI:** Pule a verificação de proteção e pule a criação do PR. Apenas commit + push, e avise o usuário a tratar o merge manualmente.
