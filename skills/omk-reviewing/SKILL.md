---
name: omk-reviewing
description: "Code and plan review with multi-angle dispatch. Trigger when user says 'review', 'code review', 'check my code', 'PR review', '@review', or when completing a plan phase that requires review. Also trigger before merge, after major feature completion, or when user asks for feedback on implementation quality."
---

## Trigger Examples
- "@review 看看这个 PR"
- "帮我 review 一下这段代码"
- "check my implementation before I merge"
- "review the plan I just wrote"
- "这个改动有没有问题？"

# Reviewing - Solicitar, executar, receber

## Solicitando review

**Quando (obrigatório):** após concluir feature grande, antes de merge, depois de cada batch de tasks.

### Plan Review, 4 ângulos, 4 subagents em paralelo

#### Identificação prévia de risco
Antes de despachar reviewers, o agent principal DEVE rodar a **Pre-mortem Analysis** definida em `skills/planning/SKILL.md` (Phase 1.5 → seção Pre-mortem Analysis). Isso produz 3 perguntas de risco (Integration / Assumption / Environment) que são injetadas como "Specific Questions" na query de dispatch de cada reviewer.

Adicionalmente, formule uma pergunta canary por dispatch que exija a leitura de um arquivo-fonte específico.

#### Dispatch

Despache exatamente **4 subagents reviewers em paralelo** (`agent_name: "reviewer"`, `dangerously_trust_all_tools: true`), um por ângulo:

| # | Ângulo | Missão |
|---|-------|---------|
| 1 | Goal Alignment | Toda task mapeia para o goal? Ordem de execução é válida? Non-goals respeitados? |
| 2 | Verify Correctness | Cada comando verify é sólido? Falsos positivos/negativos? |
| 3 | Completeness | Todos os arquivos modificados cobertos? Edge cases? Conflitos com outros plans? |
| 4 | Technical Feasibility | Bloqueadores? Contradições? Race conditions? Signal safety? |

Cada query de subagent deve incluir: caminho do arquivo do plan + caminhos dos arquivos-fonte relevantes a serem lidos.

### Pre-check determinístico (agent principal, antes de despachar reviewers)

Antes de despachar qualquer subagent reviewer, o **agent principal** roda checks determinísticos (o subagent reviewer só tem read/write/shell, sem tools de LSP):

1. Rode `get_diagnostics` em todos os arquivos modificados, colete erros/warnings de compilador
2. Rode `pattern_search` para anti-padrões conhecidos (bare except, subprocess sem timeout, etc.)
3. Empacote os resultados como "Pre-check Findings" para incluir na query de dispatch de cada reviewer

Pre-check findings são automaticamente P0/P1, não precisam de julgamento de LLM. Isso reduz a carga do reviewer apenas para issues que exigem raciocínio.

### Code Review, dispatch baseado no tamanho

Escolha o modo de dispatch com base no tamanho do diff:

**PR pequeno (<200 linhas de diff):** Despache **1 subagent reviewer** (`agent_name: "reviewer"`, `dangerously_trust_all_tools: true`) com:
- O que foi implementado
- Referência do plan/requirements
- Range do git diff (BASE_SHA..HEAD_SHA)
- Pre-check Findings do Pre-check determinístico

**PR grande (≥200 linhas de diff):** Despache **2 subagents reviewers em paralelo** (`agent_name: "reviewer"`, `dangerously_trust_all_tools: true`):

| Agent | Ângulo | Foco |
|-------|-------|-------|
| 1 | Correctness + Security | Correção funcional, validação de entrada, auth, injection, race conditions |
| 2 | Quality + Architecture | SOLID, code smells, performance, error handling, condições de borda |

Cada agent recebe: range do diff, pre-check findings e caminhos dos arquivos-fonte relevantes. Os findings de ambos os agents são unidos e desduplicados pelo agent principal antes de apresentar ao usuário.

## Princípio de Ferro: Respeite a codebase existente

> O código existente é a baseline estável e testada em batalha. Pode estar em 85/100, não perfeito, mas funciona. Seu trabalho é revisar o **código novo**, não corrigir o código antigo através do autor do PR.

- **Revise apenas linhas novas/alteradas.** Não levante findings contra código existente inalterado, mesmo com problemas de estilo, ineficiências menores ou padrões não ideais.
- **Julgue o código novo pelos padrões da codebase existente**, não pela perfeição de livro-texto. Se o código existente usa injeção de campo via `@Autowired`, não aponte o código novo por não usar injeção via construtor. Se o código existente engole certas exceções com um log warn, o código novo fazendo o mesmo é consistente, não é bug.
- **Findings P2/P3 de "melhoria de estilo" em padrões existentes são ruído.** Só levante findings sobre código existente se for P0/P1 (vulnerabilidade de segurança, perda de dados, crash) E diretamente tocado pelo PR.
- **Refactors do tipo "while we're here" estão fora de escopo.** Se o reviewer quer sugerir melhorias no código antigo, isso vira issue de follow-up separada, não comentário de PR bloqueando o merge.

## Executando Code Review (para o reviewer agent)

### 1) Contexto pré-voo

- Rode `git diff --stat` e depois `git diff` para entender o escopo
- Se o diff for > 500 linhas, divida em batches por arquivo/módulo, revise cada batch separadamente
- Anote: file renames, novos arquivos, arquivos deletados

### 2) Verificação de SOLID + arquitetura

- Carregue `references/solid-checklist.md` para a cobertura
- Verifique violações de SRP, OCP, LSP, ISP, DIP
- Sinalize code smells comuns: long methods, feature envy, data clumps, dead code
- Aplique heurísticas de refactor onde fizer sentido

### 3) Scan de segurança

- Carregue `references/security-checklist.md` para a cobertura
- Verifique: input/output safety (XSS, injection, SSRF, path traversal), gaps de auth, secrets em código
- Verifique: race conditions (acesso concorrente, check-then-act, TOCTOU, falta de locks)
- Aponte tanto **explorabilidade** quanto **impacto**

### 4) Scan de qualidade de código

- Carregue `references/code-quality-checklist.md` para a cobertura
- Verifique: error handling (exceções engolidas, catch muito amplo, async errors)
- Verifique: performance (N+1 queries, operações CPU-intensivas em hot paths, falta de cache, memória sem limite)
- Verifique: condições de borda (null/undefined, coleções vazias, limites numéricos, off-by-one)
- Sinalize issues que possam causar falhas silenciosas ou incidentes em produção

### 5) Candidatos para remoção

- Carregue `references/removal-plan.md` para o template
- Identifique código morto, imports não usados, padrões deprecated
- Categorize: seguro para remover agora vs. adiar com plan

### 6) Saída

- Carregue `references/output-format.md` para a estrutura
- Categorize findings: P0 Critical / P1 High / P2 Medium / P3 Low
- Seja específico, cite file:line e mostre exemplos de código
- Nunca carimbe

### 7) Confirmação dos próximos passos

- Apresente um resumo dos findings com contagem por prioridade
- Pergunte ao usuário como prosseguir (corrigir tudo / só P0-P1 / itens específicos / sem mudanças)
- NÃO implemente alterações até o usuário confirmar explicitamente

## Recebendo review

**Princípio central:** Verifique antes de implementar. Correção técnica acima de conforto social.

1. LEIA o feedback completo sem reagir
2. ENTENDA, reformule o requisito (ou pergunte)
3. VERIFIQUE contra a realidade da codebase
4. AVALIE, é tecnicamente sólido para ESTA codebase?
5. RESPONDA, reconhecimento técnico ou pushback fundamentado
6. IMPLEMENTE um item por vez, teste cada um

### Verificação YAGNI

Antes de implementar qualquer sugestão, pergunte: "Isso resolve um problema real que temos hoje?" Rejeite generalidade especulativa, abstrações prematuras e features para necessidades hipotéticas futuras.

### Ordem de implementação

Ao implementar feedback aceito:
1. **Issues bloqueantes primeiro**, qualquer coisa que quebre build/tests
2. **Fixes simples**, typos, naming, formatação (ganhos rápidos)
3. **Mudanças complexas**, refactors, mudanças arquiteturais (maior risco, deixe por último)

### Pushback

Faça pushback quando o reviewer estiver errado, com raciocínio técnico e evidência. Mostre código, mostre testes, mostre docs.

### Reconhecendo feedback correto

Quando o feedback estiver correto, reconheça brevemente e implemente: "Agreed, fixing." Sem bajulação.

**Nunca:** "You're absolutely right!" / "Great point!" / implementar antes de verificar.
