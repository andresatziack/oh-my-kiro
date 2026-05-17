Você DEVE seguir esta sequência exata. NÃO pule nem reordene nenhum step.

## Step 1: Deep Understanding (skill: planning Phase 0)
Siga skills/omk-planning/SKILL.md Phase 0 para construir um entendimento profundo do goal. Faça perguntas de esclarecimento, pesquise se necessário e apresente o design para trabalhos criativos/arquiteturais. NÃO prossiga até o usuário confirmar a direção. Após a confirmação do usuário: `touch .brainstorm-confirmed`

## Step 2: Escrever o plan (skill: planning)
Leia skills/omk-planning/SKILL.md, depois escreva um plan em docs/plans/<date>-<slug>.md. O plan DEVE incluir: Goal, Steps com estrutura TDD, uma seção `## Review` vazia e uma seção `## Checklist` com todos os critérios de aceitação como itens `- [ ]`. O checklist é o contrato, @execute não prossegue sem ele.

**Imediatamente após escrever o arquivo do plan**, atualize o ponteiro ativo para que `@execute` consiga encontrá-lo, mesmo a partir de outra sessão:
```bash
echo "docs/plans/<plan-file>.md" > docs/plans/.active
```

### Regras de estrutura do checklist (CRÍTICO, o Ralph Loop depende disso)
1. **Todos os itens do checklist ficam na seção `## Checklist`** (conforme definido no SKILL.md). NÃO espalhe itens `- [ ]` em linha entre as Phases, o Ralph Loop e os hooks fazem parse de `## Checklist` como única fonte da verdade.
2. **Cada item do checklist DEVE incluir um comando de verify inline** no formato: `- [ ] Description | \`verify_command\`` (por exemplo, `- [ ] Gateway responds 200 | \`curl -sf http://127.0.0.1:8000/health\``). O comando de verify deve retornar exit code 0 em caso de sucesso.
3. **Itens do checklist precisam ser acionáveis, não apenas observacionais.** Ruim: `- [ ] System looks good`. Bom: `- [ ] Config validated | \`python3 -c "import json; json.load(open('config.json'))"\``.
4. **NUNCA marque `- [x]` sem rodar o comando de verify.** O `revert_failed_checks()` do Ralph Loop reverte itens cujos comandos de verify falharem.

## Step 3: Verificar se o checklist existe
Antes de despachar o reviewer, confirme que o arquivo do plan contém uma seção `## Checklist` com pelo menos um item `- [ ]`. Se estiver faltando, adicione AGORA, não prossiga para o review sem ele.

## Step 4: Plan Review (skill: planning)
Siga `skills/omk-planning/SKILL.md` Phase 1.5 para o plan review. Selecione os ângulos de review com base na complexidade do plan, despache os subagents reviewers e aplique as regras de calibração definidas lá.

## Step 5: Endereçar o feedback
Se o verdict do reviewer for REQUEST CHANGES ou REJECT:
  - Corrija o plan com base no feedback do reviewer
  - Marque decisões antigas como ~~deprecated~~ com motivo
  - Redespache o reviewer para uma segunda rodada
  - Repita até obter APPROVE

## Step 6: Confirmação do usuário
Mostre o plan final com o verdict do reviewer. O usuário confirma dizendo `@execute` (que também dispara a execução) ou apenas "confirm" / "confirmar".

## Step 7: Hand-off para Execute
Após a confirmação do usuário (incluindo via `@execute`):
1. Escreva o caminho do arquivo do plan em `docs/plans/.active` (já feito no Step 2, mas reescreva aqui para garantir a correção após eventuais mudanças no caminho do plan durante o review)
2. Limpeza: `unlink .brainstorm-confirmed 2>/dev/null || true`
3. **Auto-commit dos artefatos do plan**, ralph_loop.py exige uma working tree limpa. Faça commit apenas dos arquivos que o agent criou/modificou durante esta sessão de plan (arquivo do plan, .active, qualquer alteração em skill/prompt). NÃO use `git add -A`, o usuário pode ter edições não relacionadas em andamento. Use caminhos de arquivo explícitos:
   ```
   git add docs/plans/<plan-file>.md docs/plans/.active [other files agent touched]
   git commit -m "plan: <plan-slug> (reviewed, approved)"
   ```
   Se `git status --porcelain` ainda mostrar arquivos não rastreados/modificados após esse commit, avise o usuário: "You have uncommitted changes outside this plan. Stash or commit them before @execute."
4. Inicie o Ralph Loop:
   ```bash
   python3 scripts/ralph_loop.py
   ```
   Reporte os resultados quando ele terminar (veja commands/execute.md Step 4).

---
User's requirement:
(Se nenhum requisito for fornecido abaixo, pergunte ao usuário o que ele quer planejar antes de prosseguir.)
