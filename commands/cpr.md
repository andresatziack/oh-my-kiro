Faz commit de todas as alterações, push para o remote e cria um Pull Request. (CPR = Commit Push PR)

## Escopo
Opera apenas no repositório git atual. NUNCA faça cd para outros repositórios nem rode commit/push neles.

## Steps

### Step 1: Stage e Commit
1. `git add -A && git status --short`, mostra o que está em stage
2. Pergunte ao usuário pela commit message se nenhuma foi fornecida, ou gere uma a partir do diff
3. `git commit -m "<message>"`
4. `git push`
5. Reporte: hash do commit + resultado do push

### Step 2: Detectar a branch alvo do PR

```bash
current_branch=$(git branch --show-current)

# 1. Check reflog for source branch (works for worktree branches)
created_from=$(git reflog show "$current_branch" --format="%gs" | tail -1 | sed 's/.*Created from //')
base=$(echo "$created_from" | sed 's#refs/remotes/origin/##; s#refs/heads/##')

# 2. If source == self (created from remote tracking branch), fallback to remote default
if [ "$base" = "$current_branch" ] || [ -z "$base" ]; then
  base=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's#refs/remotes/origin/##')
  [ -z "$base" ] && base="main"
fi

echo "PR_TARGET=$base"
```

Mostre a branch alvo detectada e peça confirmação ao usuário:
- "PR target: `<base>`. Confirm? (or specify a different branch)"
- Se o usuário fornecer outra branch, use-a.

### Step 3: Criar o PR

```bash
gh pr create --base "$base" --title "<generate from commits>" --body "<summary of changes>"
```

Reporte: "PR created: <url>. Target: `<base>`."

### Step 4: Limpeza do worktree (somente se estiver em worktree)

```bash
wt_dir=$(git rev-parse --git-common-dir 2>/dev/null)
git_dir=$(git rev-parse --git-dir 2>/dev/null)
if [ "$wt_dir" != "$git_dir" ]; then
  worktree_path=$(pwd)
  cd "$(git worktree list | head -1 | awk '{print $1}')"
  git worktree remove "$worktree_path" --force
  echo "Worktree cleaned up."
fi
```

## Casos de borda
- **Sem gh CLI:** Avise o usuário e pule a criação do PR. Apenas commit + push.
- **Sem alterações para commitar:** Pule o commit, mas ainda crie o PR se houver commits enviados que ainda não estejam em um PR.
- **Usuário na branch padrão/main:** Avise "You're on the default branch, PR doesn't make sense." e aborte.

---
User's message (the text after @cpr):
