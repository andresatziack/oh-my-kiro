# Plano de integracao da memoria persistente (referencia: planning-with-files)

**Objetivo:** Incorporar ao framework a boa pratica do planning-with-files de "arquivos como memoria persistente"; cada iteracao do ralph-loop transmite contexto via arquivos em disco, e hooks auxiliares reforcam a disciplina de escrita.

**Arquitetura:** Prompt do ralph-loop ganha regras de leitura/escrita de progress.md e findings.md, hook PreToolUse injeta o contexto do plan e hook PostToolUse lembra de gravar nos arquivos.

## Tarefas

### Tarefa 1: ajustar o prompt de `scripts/ralph-loop.sh`

**Arquivos:**
- Modify: `scripts/ralph-loop.sh`

Inclua no prompt:
- No inicio, ler `progress.md` (logs e descobertas das iteracoes anteriores) e `findings.md` (resultados da pesquisa)
- Ao concluir uma task, fazer append em `progress.md`: o que foi feito, arquivos alterados, armadilhas encontradas
- Resultados de pesquisa vao para `findings.md`: decisoes tecnicas, padroes de codigo, links de referencia
- Os dois arquivos ficam no mesmo diretorio do plan

**Formato de progress.md:**
```markdown
## Iteration N — [timestamp]
- **Task:** [checklist item description]
- **Files changed:** file1, file2
- **Learnings:** [discoveries, gotchas]
- **Status:** done / skipped
```

**Formato de findings.md:**
```markdown
## [Topic]
- **Decision:** [what was decided]
- **Rationale:** [why]
- **Pattern:** [reusable code pattern if any]
```

### Tarefa 2: criar hook PreToolUse - Read Before Decide

**Arquivos:**
- Create: `hooks/feedback/inject-plan-context.sh`

Antes de cada chamada de ferramenta de **write** (matcher: `write`, nao todas as ferramentas), se `docs/plans/.active` existir e apontar para um arquivo valido, ler a secao `## Checklist` do plan (em vez das primeiras 30 linhas, extracao precisa do checklist) e injetar em stderr.

**Tratamento de erro:** `.active` ausente ou apontando para arquivo invalido -> sai silenciosamente com exit 0 sem afetar a ferramenta.

**Performance:** so dispara em write; nao afeta read/shell. Um grep no bloco do checklist e tao preciso quanto head -30 e tem custo equivalente.

**Anti-loop:** verifica o arquivo alvo da escrita; se for progress.md ou findings.md, pular a injecao para evitar interferencia.

### Tarefa 3: criar hook PostToolUse - lembrete de atualizar arquivos

**Arquivos:**
- Create: `hooks/feedback/remind-update-progress.sh`

**matcher:** `write` (mesmo matcher de auto-test/auto-lint; Kiro executa na ordem de registro, sem conflito).

Apos a escrita, lembrar: "se isso concluiu um item da checklist, atualize o plan (marque como concluido) e progress.md (registre)".

**Anti-loop:** se o arquivo alvo for o plan, progress.md ou findings.md, nao lembrar (evita loop infinito).

### Tarefa 4: registrar os hooks na configuracao

**Arquivos:**
- Modify: `.kiro/agents/default.json` (acrescentar nos arrays preToolUse e postToolUse)
- Modify: `scripts/generate-platform-configs.sh` (sincronizar)

## Checklist
- [x] prompt de `ralph-loop.sh` contem as regras de leitura/escrita de progress.md e findings.md, com a definicao de formato
- [x] `hooks/feedback/inject-plan-context.sh` criado (PreToolUse[write], injeta a secao do checklist, com anti-loop e tratamento de erro)
- [x] `hooks/feedback/remind-update-progress.sh` criado (PostToolUse[write], com lembrete e anti-loop)
- [x] os dois hooks estao registrados em `.kiro/agents/default.json` e `generate-platform-configs.sh`
- [x] scripts dos hooks estao executaveis e sem erros de sintaxe (validados com `bash -n`)

## Review (Round 1)

~~**VERDICT: REQUEST CHANGES**~~

Required changes (resolvidos):
1. ~~Impacto de performance~~ -> PreToolUse so dispara em write, nao afeta read/shell
2. ~~Conflito de matcher do hook~~ -> matcher explicito como write; sem conflito com hooks existentes que usam o mesmo matcher
3. ~~Tratamento de erro~~ -> exit 0 silencioso quando .active e invalido
4. ~~Definicao do formato dos arquivos~~ -> formatos de progress.md e findings.md adicionados
5. ~~Testes de integracao~~ -> checklist inclui validacao com bash -n
6. ~~Ordem de execucao dos hooks e loop~~ -> verificacao anti-loop: pular quando o alvo for plan/progress/findings

## Review (Round 2)
<!-- Reviewer writes here -->
