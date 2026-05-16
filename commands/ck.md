Faz checkout de uma branch em um submodule, com suporte a busca fuzzy. (CK = Checkout)

## Escopo
Opera no submodule atual ou no submodule especificado pelo usuário.

## Steps

### Step 1: Determinar o submodule alvo

Se o usuário especificar um nome de submodule, use-o. Caso contrário, detecte a partir do diretório atual:

```bash
# Check if we're inside a submodule
sm_path=$(git rev-parse --show-superproject-working-tree 2>/dev/null)
if [ -n "$sm_path" ]; then
  echo "IN_SUBMODULE=true"
else
  # List available submodules for user to pick
  git submodule --quiet foreach 'echo $sm_path'
fi
```

### Step 2: Busca fuzzy de branches

Se o usuário forneceu um nome de branch (ou nome parcial após @ck):

```bash
input="<user_input>"

# Fetch latest branches
git fetch origin --prune --quiet 2>/dev/null

# Search: local branches first, then remote
echo "=== Local branches ==="
git branch --list "*${input}*" --sort=-committerdate | head -10

echo "=== Remote branches ==="
git branch -r --list "*${input}*" --sort=-committerdate | head -10
```

Mostre os resultados ao usuário. Se houver várias correspondências, peça para o usuário escolher. Se houver exatamente uma, confirme e prossiga.

Se o usuário NÃO forneceu nome de branch, mostre as branches recentes:

```bash
echo "=== Recent branches (last 10) ==="
git branch -r --sort=-committerdate | head -10
```

### Step 3: Checkout

Dois modos baseados na intenção do usuário:

**Modo A: Checkout direto (troca a branch atual do submodule)**
```bash
git checkout <branch>
```

**Modo B: Criar worktree (para trabalho de desenvolvimento)**
```bash
branch="<selected_branch>"
sm_name=$(basename $(pwd))
wt_name="${sm_name}-$(echo $branch | sed 's#origin/##; s#/#-#g')"
wt_path="worktrees/${wt_name}"

# Create worktree at project root level
git worktree add "../../worktrees/${wt_name}" -b "$(echo $branch | sed 's#origin/##')" "$branch" 2>/dev/null \
  || git worktree add "../../worktrees/${wt_name}" "$branch"

echo "Worktree created: $wt_path (branch: $branch)"
```

Pergunte ao usuário qual modo deseja, com padrão Modo B (worktree) para feature branches.

## Casos de borda
- **Branch não encontrada:** Mostre "No branches matching '<input>'. Did you mean:" com as correspondências mais próximas.
- **Worktree já existe para a branch:** Avise e mostre o caminho do worktree existente.
- **Detached HEAD no submodule:** Avise o usuário antes do checkout.

---
User's message (the text after @ck):
