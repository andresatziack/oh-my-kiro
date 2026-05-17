---
name: omk-planning
description: "Full plan lifecycle: deep understanding → write plan with TDD checklist → parallel review → Ralph Loop execution. Trigger when user says 'plan', 'design', 'implement', 'build', 'architect', '@plan', '@execute', or describes a multi-step task that needs structured breakdown. Also trigger for feature requests, system redesigns, or migration projects."
---

## Trigger Examples
- "@plan refatorar o sistema de hooks"
- "I want to add OAuth support, help me plan it"
- "desenhe uma nova estrategia de sincronizacao de knowledge"
- "@execute continuar a execucao do plano"
- "break this feature into tasks"

# Planning, escrever, revisar, executar

## Visão geral

Uma única skill para o ciclo de vida completo do plan: write → review → execute.

## Phase 0: Deep Understanding

Antes de escrever qualquer plan, construa um entendimento profundo do goal. Pule esta phase apenas se o usuário fornecer um design doc totalmente especificado.

### Step 1: Forme o entendimento inicial

Comece com `generate_codebase_overview` para obter a estrutura de alto nível do projeto, em seguida leia código relevante, docs e commits recentes para entender o contexto. NÃO faça perguntas ainda, primeiro construa seu próprio modelo mental de:
- O que o usuário quer alcançar
- O que existe hoje (estado atual)
- O que precisaria mudar (gap analysis)

### Step 2: Faça perguntas de esclarecimento

Com base no seu entendimento, faça perguntas **uma de cada vez**. Cada pergunta deve:
- Eliminar um ramo inteiro de ambiguidade (não detalhes triviais)
- Construir sobre respostas anteriores (aprofundamento incremental)
- Oferecer opções de múltipla escolha com sua recomendação, quando possível

**Terminação dinâmica:** pare de perguntar quando a incerteza restante não afetar materialmente o plan. Não pergunte por perguntar.

**Soft cap:** máximo 5 perguntas. Se você ainda tiver incerteza após 5, declare suas suposições e prossiga.

### Step 3: Pesquisa (opcional)

Após as perguntas serem respondidas, julgue se a pesquisa é necessária:
- **Pesquisa na codebase:** quando a task toca código existente que você ainda não explorou totalmente (por exemplo, modificar um sistema de hooks, leia os hooks existentes primeiro)
- **Pesquisa web:** quando a task envolve tools externas, APIs ou boas práticas sobre as quais você não tem certeza (por exemplo, integrar uma library nova, adotar um padrão desconhecido)
- **Ambas:** quando a task combina mudanças internas com dependências externas (por exemplo, adicionar OAuth a um módulo de auth existente)
- **Pule:** quando você tem entendimento suficiente (por exemplo, renomear uma variável, corrigir um typo, refactors simples com escopo claro)

**Princípio de dimensão de pesquisa:** quando a pesquisa É necessária, cubra tanto fundamentos teóricos (papers, docs, racional do design) QUANTO prática de engenharia (implementações reais, padrões testados em batalha, armadilhas conhecidas). Um sem o outro leva a designs de torre de marfim ou soluções cargo-cult.

Esse julgamento é seu, nem todo plan precisa de pesquisa.

### Step 4: Perguntas suplementares (se houver)

Após a pesquisa, absorva o que aprendeu. Pergunte ao usuário apenas sobre descobertas que **você não consegue resolver só com a pesquisa**, coisas que exigem decisões ou preferências do usuário.

Se não houver perguntas suplementares, prossiga direto para a Phase 1.

### Step 5: Apresentação do design (opcional)

Quando a task envolver trabalho criativo/arquitetural (novas features, novos componentes, mudanças significativas de comportamento), apresente o design antes de escrever o plan:

- Divida o design em seções de 200 a 300 palavras
- Pergunte após cada seção se está parecendo correto até ali
- Cubra: arquitetura, componentes, fluxo de dados, tratamento de erro, testes
- Escreva o design validado em `docs/designs/YYYY-MM-DD-<topic>-design.md`

Pule este step para refactors simples, bug fixes ou tasks com design doc totalmente especificado.

### Step 6: Readiness Check

Antes de prosseguir para a Phase 1, verifique se a task está bem definida em 4 dimensões:

| Dimensão | ✅ Critério | Greenfield | Brownfield |
|-----------|-------------|------------|------------|
| **Goal** | da para descrever em uma frase, sem ambiguidade, o que precisa ser feito | Required | Required |
| **Constraints** | fronteiras, non-goals e restricoes ja estao explicitos | Required | Required |
| **Success Criteria** | pelo menos 2 criterios de aceite testaveis | Required | Required |
| **Context** | entendimento do codigo/sistema existente que sera modificado | Skip | Required |

Regras:
- Todas as dimensões aplicáveis precisam estar ✅ para prosseguir para a Phase 1
- Se alguma dimensão estiver ❌, faça UMA pergunta direcionada à dimensão mais fraca
- Esse step adiciona no máximo 3 perguntas (em cima das do Step 2)
- Usuário diz "skip" → declare suposições e continue

**Challenge Modes** (ativados a partir da 2ª pergunta deste step):
- **Contrarian** (2ª pergunta): "e se [premissa central] estiver errada?"
- **Simplifier** (3ª pergunta): "como seria a versao mais simples?"

### Transição para a Phase 1

#### Goal-Backward Derivation

Após o Readiness Check, faça engenharia reversa a partir dos Success Criteria antes de escrever o plan:

Para cada Success Criterion:
1. **O que precisa ser VERDADEIRO** para esse critério passar?
2. Quais dessas verdades **já existem** na codebase?
3. Quais precisam ser **criadas**? → Essas viram Tasks
4. Quais são as **dependências** entre as novas verdades? → Essas determinam a ordem das Tasks

Isso garante que o plan cubra tudo o que é necessário para o goal, não apenas o que parece óbvio do ponto de vista forward.

#### Auto-verificação Socrática

Em seguida, valide cada decisão de design importante:
1. **Essência**, qual é o problema central que essa decisão resolve?
2. **Framework**, a codebase atual já resolve isso? Quais padrões conhecidos se aplicam?
3. **Aplicação**, isso é viável em todas as plataformas alvo? O benefício > custo de manutenção?

Descarte qualquer decisão que falhe no step 2 (já resolvido) ou no step 3 (inviável/não vale).

Em seguida, prossiga para a Phase 1 com o entendimento acumulado.

### Tratamento de erros

- **Sem código/docs relevantes encontrados:** informe ao usuário, peça que aponte a área certa e continue.
- **Usuário quer pular a Phase 0:** permitido. O usuário pode dizer "skip questions" ou "just write the plan" a qualquer momento. Declare suas suposições e prossiga para a Phase 1.
- **Respostas contraditórias:** traga a contradição à tona, peça para o usuário esclarecer qual direção seguir.
- **Cap de 5 perguntas atingido com ambiguidade crítica:** declare suposições restantes explicitamente e prossiga para a Phase 1. O plan vai registrar essas suposições para escrutínio do reviewer.

## Phase 1: Escrevendo o plan

**Salve em:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

### Header do plan (obrigatório)

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence]
**Non-Goals:** [What this plan explicitly does NOT do]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Key technologies]
**Work Dir:** [Relative path to working directory, e.g. `src/` or `.`]

## Review
<!-- Reviewer writes here -->
```

### Formato do Checklist (obrigado pelo hook)

Todo plan precisa de uma seção `## Checklist`. Cada item do checklist DEVE incluir um comando verify executável:

```markdown
- [ ] description | `verify command`
```

Exemplos:
- `- [ ] sintaxe do hook correta | \`bash -n hooks/security/my-hook.sh\``
- `- [ ] config inclui o novo hook | \`jq '.hooks' .kiro/agents/pilot.json | grep -q my-hook\``
- `- [ ] paths externos sao bloqueados | \`echo '{"tool_name":"fs_write","tool_input":{"file_path":"/tmp/evil.txt"}}' | bash hooks/security/my-hook.sh 2>&1; test $? -eq 2\``

Regras:
- O comando verify precisa ser executável (sem "teste manual", sem "inspecao visual")
- O comando verify precisa retornar exit 0 em caso de sucesso
- Cada Task precisa de pelo menos 1 item de checklist
- Cubra: caminho feliz + edge case + integração (quando aplicável)
- O hook obriga: marcar `- [x]` exige execução bem-sucedida recente do comando verify
- **Regra de regression test:** se os campos Files do plan incluírem `scripts/ralph_loop.py` ou `scripts/lib/`, o checklist DEVE incluir: `- [ ] regression tests passando | \`python3 -m pytest tests/ralph-loop/ -v\``
- **Regra de vertical slice:** organize tasks como vertical slices (uma feature de ponta a ponta) em vez de camadas horizontais (todos os models, depois todas as APIs). Vertical slices têm menos dependências entre tasks, permitindo commits atômicos mais limpos. Exceção: tasks que são inerentemente horizontais (por exemplo, "add logging to all hooks") não precisam ser forçadas em vertical slices.

### Itens de checklist coarse

Itens de checklist podem ser de alto nível ("coarse"), desde que o comando verify seja significativo. O agent executor usa o Reasoning Loop (OBSERVE → THINK → PLAN → EXECUTE → REFLECT → CORRECT → VERIFY) para decompor de forma autônoma itens coarse em sub-steps concretos.

**Exemplos fine-grained vs. coarse:**

| Estilo | Item | Quando usar |
|-------|------|-------------|
| Fine | `- [ ] Add timeout param to fetch() \| \`grep -q 'timeout' src/fetch.py\`` | Tasks simples, alteração única |
| Coarse | `- [ ] Implement user auth module \| \`python3 -m pytest tests/auth/ -v\`` | Tasks de múltiplos steps em que o agent decide os detalhes |

**Regras para itens coarse:**
- O comando verify ainda precisa ser executável e retornar exit 0, isso é não negociável
- Prefira comandos de teste em nível de módulo ou integração como verify (por exemplo, `python3 -m pytest tests/module/ -v`)
- O corpo da Task deve descrever o objetivo e as constraints, não cada linha de código
- O agent executor decompõe autonomamente usando o Reasoning Loop

### Estrutura da Task (TDD)

Cada task segue red-green-refactor:

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write failing test**
[Complete test code]

**Step 2: Run test — verify it fails**
Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL

**Step 3: Write minimal implementation**
[Complete implementation code]

**Step 4: Run test — verify it passes**
Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**
```

Regras: paths exatos, código completo (não "add validation"), comandos exatos com saída esperada.

### Seção Errors (obrigatória)

Todo plan precisa de uma seção `## Errors` no fim. Durante a execução, registre cada erro encontrado:

```markdown
## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|
```

Regras:
- Logue imediatamente quando o erro ocorrer, não espere
- Inclua qual Task disparou o erro
- Acompanhe o número da tentativa, se o mesmo erro aparecer na tentativa 3, dispare o 3-Strike Protocol (veja Phase 2)
- Esta seção é append-only durante a execução, nunca apague entradas
- Cap: mantenha as 20 entradas mais recentes, se exceder, resuma as antigas em uma única linha "Earlier errors: N resolved"

### Seção Findings (opcional)

Plans podem incluir uma seção `## Findings` para persistir descobertas de pesquisa feitas durante a execução:

```markdown
## Findings

- [discovery with context]
```

Regras:
- Append-only, nunca reescreva, apenas adicione novas entradas
- Use quando a pesquisa em fase de execução revelar algo relevante para tasks posteriores
- Não é obrigatório para plans simples em que nenhuma pesquisa acontece durante a execução

### Seção Session State (opcional)

Plans podem incluir uma seção `## Session State` para continuidade entre sessões:

```markdown
## Session State

**Position:** Task N of M
**Last session:** YYYY-MM-DD HH:MM
**Decisions made this session:**
- [decision with rationale]

**Notes for next session:**
- [what to pick up, what to watch out for]
```

Regras:
- Atualizada ao final de cada rodada do Ralph Loop (antes de o agent sair)
- Lida no início de cada rodada (parte do Session Resume Protocol)
- Append-only para decisions, position e notes são sobrescritas a cada rodada
- Não é obrigatória para plans pequenos (≤ 3 itens) que terminam em uma única rodada

## Phase 1.5: Plan Review

Após escrever o plan, rode plan review multi-perspectiva antes da execução.

### Pool de ângulos

Duas categorias: **fixos** (toda rodada) e **aleatórios** (amostrados a cada rodada).

**Ângulos fixos (sempre incluídos):**

| Ângulo | Missão | Saída |
|-------|---------|--------|
| Goal Alignment | You MUST copy each table below and fill EVERY cell. Do NOT summarize or skip rows. If a table has N tasks, your output must have N rows. Missing rows = review REJECTED. Copy and fill this table for EVERY task:\n\n\| Task # \| Goal phrase served (quote exact words) \| If removed, which Goal phrase loses coverage? \|\n\|--------\|---------------------------------------\|----------------------------------------------\|\n\| 1 \| [quote] \| [answer] \|\n\nThen copy and fill the coverage matrix:\n\n\| Goal phrase (copy from plan header) \| Covered by Task #s \|\n\|-------------------------------------\|-------------------\|\n\| [phrase 1] \| [list] \|\n\nFinally: trace the execution order — does Task N's output feed correctly into Task N+1's input? Findings must cite specific Task numbers and Goal phrases. | Missing Coverage / Unnecessary Tasks / Ordering Issues / Verdict |
| Verify Correctness | For each checklist verify command, you MUST copy this table and fill in EVERY cell:\n\n\| # \| Verify command \| Confirms what \| Exit code (correct impl) \| Exit code (broken impl) \| Sound? \|\n\|---\|---------------\|---------------\|--------------------------|--------------------------|--------\|\n\| 1 \| [copy from plan] \| [fill] \| [trace: ... → exit ?] \| [trace: ... → exit ?] \| [Y/N + reason] \|\n\nRules: EVERY row must show the shell execution trace, not just "exit 0". If you skip a row or write "all sound" without per-row traces, your review is REJECTED. Only flag commands where correct and broken give the SAME exit code. | False Positives / Weak Verifications / Verdict |

**Pool aleatório (2 amostrados por rodada):**

| Ângulo | Missão | Método de análise | Saída |
|-------|---------|-----------------|--------|
| **All angles** | Before writing any finding, verify it is within the plan's stated Goal and NOT in Non-Goals. Findings outside scope are noise — discard silently. | — | — |
| Completeness | You MUST copy each table below and fill EVERY cell. Missing rows = review REJECTED.\n\nFor each file in the plan's Files: fields that is MODIFIED (not created), copy and fill:\n\n\| File \| Function/Branch \| Exercised by Task # \| Coverage? \|\n\|------\|----------------\|--------------------\|-----------\|\n\| [path] \| [name] \| [task # or NONE] \| [Y/N] \|\n\nThen for each error path (try/except, if-error-return, signal handler) in modified files:\n\n\| File:line \| Error path \| Exercised by Task # \|\n\|----------\|------------|--------------------\|\n\| [path:line] \| [description] \| [task # or NONE] \|\n\nSCOPE: Only analyze functions/branches in files the plan MODIFIES. Do NOT flag functions in files the plan merely reads. | Source-to-task traceability matrix | Uncovered Functions / Unexercised Error Paths / Verdict |
| Testability | You MUST copy this table and fill EVERY cell. Missing rows = review REJECTED.\n\nFor each Task's test case:\n\n\| Task # \| Assertion (what property) \| Minimal wrong impl that passes \| False negative? \|\n\|--------\|--------------------------|-------------------------------|----------------\|\n\| [N] \| [what is checked] \| [describe wrong impl] \| [Y/N + reason] \|\n\nOnly flag tests where you can construct a concrete wrong implementation that passes. "Might be weak" without a specific wrong impl = not actionable. | False negative analysis per test | Weak Assertions / False Negative Risks / Verdict |
| Technical Feasibility | For each Task: 1) list external dependencies (libraries, OS features, file system assumptions), 2) check if any dependency has platform/version constraints that conflict with Tech Stack, 3) for subprocess-based tests, verify timeout values are sufficient for the operations described, 4) for tests that run commands in tmp_path or isolated dirs, trace whether the command will behave correctly outside the project root (e.g. pytest rootdir detection, missing config files). Flag only concrete blockers, not theoretical risks. | Dependency + constraint audit | Blockers / Platform Risks / Verdict |
| Security | For each Task that touches file I/O, subprocess, or signal handling: 1) trace data flow from external input to execution, 2) check for path traversal, command injection, or symlink attacks in test fixtures, 3) verify temp files use secure creation (tmp_path, not hardcoded paths). | Data flow trace per Task | Injection Surfaces / Unsafe Patterns / Verdict |
| Compatibility & Rollback | For each modified file in the plan: 1) list existing tests that import or call functions in that file, 2) check if the plan's changes could break those existing tests, 3) verify the plan includes running existing tests (not just new ones). Also: can the plan's changes be reverted with a single `git revert`? | Existing-test impact analysis | Breaking Changes / Revert Safety / Verdict |
| Performance | For each Task involving subprocess or threading: 1) calculate worst-case wall-clock time (timeout × max_iterations × retry count), 2) sum across all Tasks to get total suite time, 3) flag any single test that could exceed 30s without @pytest.mark.slow. Provide concrete numbers, not estimates. | Quantified time budget per Task | Time Budget Table / Slow Test Violations / Verdict |
| Clarity | For each Task's "What to implement" section: 1) attempt to write the function signature and key assertions from the description alone (without reading source), 2) flag any Task where you cannot determine the exact test structure from the description. A clear plan = an executor agent can implement without reading source first. | Implementability dry-run | Ambiguous Tasks / Missing Specs / Verdict |

### Pre-mortem Analysis

Antes de selecionar os ângulos de review, suponha que o plan já foi executado e **falhou**. Identifique as 3 causas mais prováveis de falha:

1. **Riscos de integração**, as alterações vão quebrar comportamento existente ou conflitar com outros componentes?
2. **Riscos de suposição**, quais suposições implícitas podem estar erradas? (por exemplo, formato de arquivo, comportamento de API, ordem de execução)
3. **Riscos de ambiente**, isso vai funcionar em todos os ambientes alvo? (por exemplo, CI, OS diferentes, dependências faltando)

Para cada risco, formule uma pergunta concreta e verificável. Injete-as como "Specific Questions" na query de dispatch de cada reviewer (veja Dispatch Query Template abaixo).

### Seleção de ângulos

Toda rodada: 2 fixos + 2 aleatórios = 4 reviewers (um único batch paralelo, sem overflow).

Seleção aleatória: amostre 2 do pool aleatório. Repetições entre rodadas estão ok, o mesmo ângulo revisando um plan revisado pega regressões e verifica fixes.

### Dispatch Query Template

Cada query de reviewer DEVE incluir: Context (Goal, Non-Goals, decisões-chave de design), Mission (específica do ângulo, da tabela acima), arquivos a ler e anti-padrões.

```
## Context
Goal: [one sentence from plan header]
Non-Goals: [from plan header]
Key design decisions that reviewers might mistake for gaps:
- [decision 1 — what was chosen and what was intentionally excluded]
- [decision 2]

## Your Mission
This is a PLAN REVIEW (Mode 1 in your prompt).
[angle-specific mission from the table above]

## Read These Files
Plan: [path]
Source files referenced in plan: [list — reviewer must read before claiming code behavior]

## Anti-patterns (do NOT do these)
- Do not flag issues outside the stated Goal/Non-Goals
- Do not suggest alternative approaches that are equally valid
- Do not flag missing implementation details that an executor agent can infer
- [plan-specific anti-patterns if any]

## Specific Questions for This Plan
Answer each question with evidence (file:line or shell output). Unanswered = review REJECTED.
1. [risk question identified by main agent]
2. [risk question identified by main agent]

## Source Reading Canary
Answer this BEFORE your analysis. Wrong answer = review REJECTED.
Q: [question only answerable by reading specific source file, e.g. "What is the first line of function X in file Y?"]

## Mandatory Source Reading
Before making ANY claim about code behavior, you MUST:
1. Read the actual source file (use Bash: cat <file>)
2. Cite the specific line number in your finding
3. If you haven't read the file, do NOT speculate — read it first
Findings about code behavior without file:line citations will be discarded.

## Output Requirements
Your last line MUST be exactly one of:
  Verdict: APPROVE
  Verdict: REQUEST CHANGES
Missing verdict = review REJECTED and will be re-dispatched.
```

### Orquestração

1. Componha a rodada: Goal Alignment + Verify Correctness + 2 ângulos aleatórios
2. Despache 4 subagents reviewers em UMA chamada `use_subagent` (`dangerously_trust_all_tools: true` para cada). A query do reviewer = missão do ângulo de review + caminho do arquivo do plan. O reviewer lê o arquivo sozinho (tem tools de read/shell). NÃO cole o conteúdo do plan na query, isso aumenta o payload e quebra o paralelismo de 4 vias. **Passe o caminho do arquivo do plan, não o conteúdo.** **É preciso especificar `agent_name: "reviewer"`**. O mesmo `agent_name` pode lançar várias instâncias em paralelo. **Inclua em cada query:** "Read the source files referenced in the plan before making claims about code behavior."
4. Reviewers da mesma rodada NÃO veem o feedback uns dos outros
5. Colete todos os verdicts. Se ALGUM reviewer der REJECT → corrija os issues → próxima rodada (re-amostre 2 ângulos aleatórios)
   **Enforcement do verdict:** se a saída de um reviewer não terminar com `Verdict: APPROVE` ou `Verdict: REQUEST CHANGES`, trate como malformada → redespache esse ângulo único.
6. **Regra para Round 2+:** ao redespachar após fixes, inclua em cada query uma seção "Rejected Findings" com resumos de uma linha dos findings rejeitados em rodadas anteriores e o motivo. Reviewers não devem voltar a levantá-los.
   **Contagem de reviewers em Round 2+:** despache apenas 2 reviewers (os 2 ângulos fixos: Goal Alignment + Verify Correctness). NÃO amostre ângulos aleatórios em Round 2+. O propósito do Round 2+ é verificar fixes, não descobrir issues novos.
7. Repita até todos darem APPROVE em uma única rodada, ou até atingir 3 rodadas
8. Após 3 rodadas: pare e diga ao usuário "Plan too complex for automated review. Consider breaking into smaller plans."

### Calibração do reviewer

Reviewers só devem dar REJECT por issues que fariam o plan falhar ou produzir resultados errados. NÃO rejeite por:
- Preferências de estilo ou abordagens alternativas igualmente válidas
- Riscos teóricos pouco prováveis na prática
- Features faltantes que são "nice to have" mas não exigidas pelo goal declarado do plan

A barra é "esse plan vai produzir um resultado 90/100?", não "esse plan está perfeito?"

### Resolução de conflitos

Quando reviewers dão feedback contraditório:
1. O agent principal compara ambos os argumentos contra a declaração de **Goal** do plan (a frase única no header)
2. O argumento que serve diretamente ao Goal vence
3. Documente o conflito, ambos os argumentos e a resolução na seção Review do plan
4. Se ambos os argumentos servem o goal igualmente, peça ao usuário para decidir

### Constraints de recursos

- **Máximo de subagents paralelos por batch**: 4 (limite hard da tool). Round 1: 4 reviewers. Round 2+: 2 reviewers (apenas ângulos fixos).
- **Isolamento de contexto do reviewer**: reviewers da mesma rodada NÃO veem o feedback uns dos outros. Cada um recebe o plan completo.
- **Tamanho do contexto**: review packet = conteúdo completo do arquivo do plan (verbatim). Reviewers precisam dos detalhes completos das tasks, blocos de código e file paths para evitar rejeições falsas por informação incompleta.
- **Tratamento de erro**: se um reviewer der crash ou retornar saída malformada, continue com os reviewers restantes. Se menos da metade dos reviewers da rodada terminar, reinicie a rodada. Malformado = sem estrutura Mission/Findings/Verdict.

## Phase 2: Execução

Após o plan ser revisado e aprovado, escolha a estratégia de execução com base no tamanho do checklist:

### Disciplinas de execução

Estas regras se aplicam independentemente da estratégia de execução escolhida.

#### Session Resume Protocol

Ao iniciar ou retomar a execução (incluindo novas sessões):
1. Leia o Goal + Architecture + Non-Goals do plan
2. Rode `git diff --stat` para ver o que já mudou
3. Verifique o checklist: quais itens estão `[x]` concluídos, quais `[ ]` permanecem
4. Escreva um resumo de status de uma linha na seção `## Findings` do plan

Isso garante que o agent tenha contexto completo antes de fazer qualquer alteração.

#### Read Before Decide

Antes de qualquer destas ações, releia o **Goal** e os **Non-Goals** do plan:
- Mudar a abordagem de implementação no meio da task
- Decidir pular ou reordenar uma task
- Encontrar um bloqueio e escolher um workaround
- Adicionar escopo que não estava no plan original

Isso traz o intent original de volta para a janela de atenção, prevenindo drift após muitas tool calls.

#### Reorientação periódica

A cada 3 tasks concluídas, releia o parágrafo **Goal** do plan. Sem necessidade de escrever, é puro refresh de atenção. Isso contraria o decay gradual de contexto em sessões longas.

#### 3-Strike Error Protocol

Quando ocorrer um erro durante a execução:

**Strike 1, Diagnose & Fix:** Leia o erro com cuidado, identifique a causa raiz, aplique fix direcionado. Logue em `## Errors`.

**Strike 2, Alternative Approach:** Mesmo erro? Tente um método fundamentalmente diferente. Tool diferente, algoritmo diferente, ângulo diferente. Logue em `## Errors`.

**Strike 3, Broader Rethink:** Questione suposições. Pesquise soluções. Considere se o próprio plan precisa de revisão. Logue em `## Errors`.

**Após 3 strikes:** pare e escale para o usuário. Explique o que foi tentado, compartilhe os erros específicos e peça orientação. NÃO tente uma 4ª vez com a mesma abordagem.

Regras:
- `next_action != failed_action`, nunca repita exatamente a mesma abordagem que falhou
- Cada strike deve ser logado na tabela `## Errors` do plan com o número da tentativa
- A contagem de strikes é por tipo de erro, não global (erros diferentes têm seus próprios 3 strikes)

### Estratégia de execução

Execução sequencial: uma task por vez, commit após cada uma.

1. Carregue o plan, identifique o próximo item não marcado
2. Execute a task (implementar + testar + verificar)
3. Marque o item, faça commit
4. Continue para a próxima. Repita até concluir.

Cada iteração do ralph loop lança uma CLI nova com contexto limpo. O agent deve concluir o máximo de tasks possível por iteração antes de o contexto encher.

## Phase 3: Conclusão

Depois que todas as tasks estiverem concluídas:
1. Rode a suíte de testes completa
2. Apresente as opções: merge local / criar PR / manter branch / descartar
3. Limpe o worktree, se aplicável

## Quando parar e perguntar

- Encontrar um bloqueio (dependência faltando, instrução pouco clara)
- Verificação falha repetidamente
- O plan tem gaps críticos
- Não force a passagem por bloqueios, pare e pergunte.
