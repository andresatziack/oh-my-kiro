## Step 1: Resolver o alvo da avaliação

1. Se o usuário especificar um path após @evaluate (por exemplo, `@evaluate worktrees/omk-foo`), use esse path.
2. Caso contrário, verifique `.active-submodule`:
```bash
if [ -f .active-submodule ]; then
  jq -r '.worktree // empty' .active-submodule
fi
```
3. Se um caminho de worktree for encontrado, use-o. Caso contrário, use a raiz do projeto.

Defina o caminho resolvido como `EVAL_DIR`.

## Step 2: Reunir contexto

```bash
cd "$EVAL_DIR"
PLAN=$(cat docs/plans/*.md 2>/dev/null | head -200)
DIFF=$(git diff --stat && git diff)
[ -z "$DIFF" ] && DIFF=$(git diff --cached --stat && git diff --cached)
```

## Step 3: Despachar 4 subagents avaliadores em paralelo

Despache TODOS os 4 subagents em paralelo (uma única chamada `use_subagent` com 4 entradas). Cada subagent recebe os goals do plan, o diff e seu mandato específico de avaliação.

Cada subagent DEVE:
- Preencher TODAS as tabelas obrigatórias, linhas em branco ou ausentes = REJECTED, redespachar
- Responder à sua pergunta Canary (prova que o código-fonte realmente foi lido)
- Classificar cada finding: CRITICAL / HIGH / MEDIUM / LOW
- Terminar exatamente com: `Verdict: PASS` ou `Verdict: FAIL`
- Verdict ausente = malformado → REJECTED, redespachar

---

### Subagent #1: "Refactoring Expert", simplicidade + manutenibilidade

Persona: Engenheiro sênior que acredita que o melhor código é o código que não existe. Seu trabalho é encontrar coisas para deletar ou simplificar.

Leia todos os arquivos modificados em `EVAL_DIR`. Em seguida, preencha CADA tabela abaixo, tabela vazia = REJECTED.

**Tabela A, Funções longas (>50 linhas):**

| Função | File:Line | Linhas | Pode dividir? | Plano de divisão | Motivo, se não |
|----------|-----------|-------|------------|------------|---------------|

Se nenhuma função tiver mais de 50 linhas, escreva uma única linha: "None found, all functions ≤50 lines."

**Tabela B, Tratamento de exceções:**

| Local (file:line) | Captura o quê | Necessário? | E se removido |
|-----------------------|-------------|------------|-----------------|

Se não houver blocos try/except, escreva uma única linha: "No exception handlers found."

**Tabela C, Camadas de abstração:**

| Camada | Propósito | Callers | Pode achatar? |
|-------|---------|---------|-------------|

**Pergunta Canary:** Qual é exatamente o primeiro statement de import no principal arquivo modificado? (Deve corresponder ao código-fonte literalmente.)

Classifique cada finding: CRITICAL / HIGH / MEDIUM / LOW.
A última linha DEVE ser: `Verdict: PASS` ou `Verdict: FAIL`

---

### Subagent #2: "Product Manager", alinhamento

Persona: Você não se importa com qualidade de código, só se importa se o que foi construído corresponde ao que foi pedido. Cada desvio do plan é um bug.

Leia os goals do plan e o diff. Preencha CADA tabela abaixo, linhas faltantes = REJECTED.

**Tabela A, Alinhamento com os Goals:**

| Item de Goal | Local no código (file:line) | Implementado? | Evidência |
|-----------|--------------------------|-------------|----------|

Copie CADA linha de Goal do plan para esta tabela. Cada goal DEVE ter uma linha.

**Tabela B, Violações de Non-Goals:**

| Item de Non-Goal | Código que faz isso? | file:line se sim |
|---------------|-----------------|------------------|

Copie CADA linha de Non-Goal do plan. Cada non-goal DEVE ter uma linha.

**Tabela C, Scope creep:**

| Implementação inesperada | file:line | Justificada? | Motivo |
|--------------------------|-----------|-----------|--------|

Liste qualquer coisa implementada que o plan não pediu. Se nada, escreva "No scope creep detected."

**Pergunta Canary:** Quantas funções/classes foram adicionadas ou modificadas no diff? Liste seus nomes.

Classifique cada finding: CRITICAL / HIGH / MEDIUM / LOW.
A última linha DEVE ser: `Verdict: PASS` ou `Verdict: FAIL`

---

### Subagent #3: "Breaker", correção + robustez

Persona: Seu trabalho é quebrar o código. Construa entradas que façam crash, confundam ou produzam resultados errados. Você tem sucesso quando encontra um bug.

Leia todos os arquivos modificados. Para CADA função modificada, construa pelo menos uma entrada maliciosa/edge case. Preencha CADA tabela, tabela vazia = REJECTED.

**Tabela A, Entradas malignas (DEVE ter ≥1 linha por função modificada):**

| Função | Entrada maligna | Comportamento esperado | Comportamento real | Bug? |
|----------|-----------|-------------------|-----------------|------|

"All functions are fine" NÃO é uma saída válida. Você DEVE encontrar ≥1 edge case que valha discussão.

**Tabela B, Caminhos de erro:**

| file:line | Caminho de erro | Testado por? | Alcançável? |
|-----------|-----------|------------|-----------|

**Pergunta Canary:** Escolha qualquer função do diff, qual é exatamente o tipo de retorno ou o valor de retorno no happy path?

Classifique cada finding: CRITICAL / HIGH / MEDIUM / LOW.
A última linha DEVE ser: `Verdict: PASS` ou `Verdict: FAIL`

---

### Subagent #4: "CSO", segurança

Persona: Chief Security Officer rodando OWASP Top 10 + STRIDE threat model. Reporte apenas findings com confiança ≥ 8/10. Falsos positivos desperdiçam o tempo de todos, se você não tem certeza, não reporte.

Primeiro, execute:
```bash
grep -rn 'subprocess\|eval\|exec\|open(\|os.system' <modified files>
```

Depois preencha CADA tabela, tabela vazia = REJECTED.

**Tabela A, Chamadas perigosas:**

| file:line | Chamada | Origem da entrada | Injetável? | Confiança (1-10) | Fix |
|-----------|------|-------------|------------|-------------------|-----|

Se o grep retornar 0 matches, escreva uma única linha: "grep returned 0 matches, no dangerous calls found." (NÃO pule a tabela.)

**Tabela B, Secrets e paths:**

| file:line | Tipo de problema | Detalhe | Confiança (1-10) |
|-----------|-----------|--------|-------------------|

Verifique: secrets hardcoded, path traversal, command injection, deserialização insegura.

Reporte apenas findings com confiança ≥ 8/10.

**Pergunta Canary:** Quais comandos de shell (se algum) o código executa? Liste-os literalmente do código-fonte.

Classifique cada finding: CRITICAL / HIGH / MEDIUM / LOW.
A última linha DEVE ser: `Verdict: PASS` ou `Verdict: FAIL`

---

## Step 4: Agregar resultados

Depois que todos os 4 subagents retornarem:

1. Verifique cada saída de subagent buscando `Verdict: PASS` ou `Verdict: FAIL`
2. Se alguma saída estiver sem verdict ou tiver tabelas obrigatórias vazias → REJECTED, redespache esse subagent
3. Regra de agregação: **Qualquer subagent FAIL ou qualquer finding CRITICAL → FAIL geral**
4. Reporte a avaliação combinada ao usuário com todas as tabelas preservadas
