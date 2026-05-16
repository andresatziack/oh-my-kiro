Gerencia worktrees: lista status e limpa branches já mergeadas.

## Step 1: Listar todas as worktrees com status

Execute:
```bash
echo "=== Worktrees in worktrees/ ==="
for dir in worktrees/*/; do
  [ -d "$dir" ] || continue
  dir="${dir%/}"
  BRANCH=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
  echo "  $dir → branch: $BRANCH"
done
```

## Step 2: Verificar status de merge

Para cada worktree, detecte seu submodule lendo o arquivo `.git` e verifique o status de merge:

```bash
for dir in worktrees/*/; do
  [ -d "$dir" ] || continue
  dir="${dir%/}"
  NAME=$(basename "$dir")
  BRANCH=$(git -C "$dir" rev-parse --abbrev-ref HEAD 2>/dev/null || continue)

  # Detect submodule from worktree's git common dir
  COMMON=$(git -C "$dir" rev-parse --git-common-dir 2>/dev/null)
  SM=$(basename "$(dirname "$COMMON")" 2>/dev/null)
  [ -d "$SM" ] || { echo "  ⚠️ $dir — cannot detect submodule, skipping"; continue; }

  # Check if branch is merged into main
  git -C "$SM" fetch origin main --quiet 2>/dev/null
  if git -C "$SM" branch --merged origin/main 2>/dev/null | grep -q "$BRANCH"; then
    echo "  ✅ $dir ($BRANCH) — MERGED into $SM/main → safe to remove"
  else
    echo "  🔄 $dir ($BRANCH) — NOT merged into $SM/main"
  fi
done
```

## Step 3: Confirmar e limpar

Mostre a lista ao usuário. Para worktrees marcadas como "MERGED":
- Peça ao usuário para confirmar quais devem ser removidas
- Para cada remoção confirmada:
```bash
git -C <submodule> worktree remove ../worktrees/<name>
```
- Se `.active-submodule` existir e seu campo worktree corresponder ao path removido, limpe-o:
```bash
if [ -f .active-submodule ] && command -v jq >/dev/null 2>&1; then
  WT=$(jq -r '.worktree // ""' .active-submodule 2>/dev/null)
  [ "$WT" = "worktrees/<name>" ] && : > .active-submodule
fi
```

## Regras importantes
- Gerencie apenas worktrees dentro do diretório `worktrees/` (não paths externos)
- Sempre confirme com o usuário antes de remover, nunca delete automaticamente
- Use `git -C <submodule> worktree remove` (não rm -rf)

---
User's message (the text after @wt):
