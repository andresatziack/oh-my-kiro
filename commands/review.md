Antes de despachar o reviewer, determine o diretório de trabalho correto:

## Step 1: Resolver o alvo do review

1. Se o usuário especificar um path após @review (por exemplo, `@review worktrees/omk-foo`), use esse path.
2. Caso contrário, verifique se `.active-submodule` existe na raiz do projeto:
```bash
if [ -f .active-submodule ]; then
  jq -r '.worktree // empty' .active-submodule
fi
```
3. Se um caminho de worktree for encontrado, use-o como diretório de trabalho do review.
4. Se nenhum dos dois estiver disponível, faça o review na raiz do projeto (comportamento padrão).

Defina o caminho resolvido como `REVIEW_DIR`.

## Step 2: Coletar contexto do diff

Rode no diretório resolvido para construir a query de review:
```bash
cd "$REVIEW_DIR"
git diff --stat
git diff
```

Se o diff estiver vazio (sem alterações fora de stage), verifique também as alterações em stage:
```bash
cd "$REVIEW_DIR"
git diff --cached --stat
git diff --cached
```

## Step 3: Despachar o reviewer

Despache um subagent reviewer (`agent_name: "reviewer"`) com esta query:

"Review the code changes in `<REVIEW_DIR>`. Run `git -C <REVIEW_DIR> diff --stat` then `git -C <REVIEW_DIR> diff`. If no unstaged changes, check `git -C <REVIEW_DIR> diff --cached`. Categorize findings: P0 Critical / P1 High / P2 Medium / P3 Low. Check: correctness, security, SOLID violations, test coverage, edge cases. Be specific, cite file:line and show code examples."

Reporte os findings para mim.
