# Referência de Depuração

## Receitas das tools de LSP

### get_diagnostics, erros e warnings de compilador

Obtenha todos os erros, warnings e hints de um arquivo:
```
get_diagnostics(file_path="src/main.py")
```
Use PRIMEIRO ao depurar, dá os locais e tipos exatos do erro.
Use DEPOIS do fix, verifique zero novos diagnostics introduzidos.

### search_symbols, encontrar definições de símbolos

Encontre onde uma função, classe ou variável é definida:
```
search_symbols(symbol_name="processOrder", symbol_type="function")
```
Use quando souber o nome mas não a localização.

### goto_definition, navegar até a implementação

Salte para onde um símbolo é realmente definido:
```
goto_definition(file_path="src/handler.py", row=42, column=15)
```
Use depois de search_symbols para ler a implementação real.
**Iron Law: sem goto_definition = sem modificar.**

### find_references, encontrar todos os locais de uso

Encontre todos os locais onde um símbolo é usado:
```
find_references(file_path="src/models.py", row=10, column=8)
```
Use antes de refatorar, para entender o impacto.
**Iron Law: sem find_references = sem refactor.**

### get_hover, informação de tipo

Obtenha tipo e documentação em uma posição:
```
get_hover(file_path="src/utils.py", row=25, column=12)
```
Use para entender tipos sem ler a implementação completa.

### Workflow típico

```
1. get_diagnostics → identify errors
2. search_symbols → find relevant code
3. goto_definition → read implementation
4. find_references → understand usage
5. get_hover → check types
6. [fix code]
7. get_diagnostics → verify fix (zero new diagnostics)
```

## Busca estrutural de código (pattern_search)

Use `pattern_search` para detecção AST-aware de padrões de bug, encontra correspondências estruturais que o grep deixa passar.

### Encontrar chamadas de subprocess sem timeout
```
pattern_search(pattern='subprocess.run($$$ARGS)', language='python')
```
Em seguida, inspecione cada match procurando o parâmetro `timeout=` faltando.

### Encontrar retornos de erro não verificados (Go)
```
pattern_search(pattern='$VAR, _ := $FUNC($$$)', language='go')
```

### Encontrar bare except clauses (Python)
```
pattern_search(pattern='except: $$$BODY', language='python')
```

### Encontrar TODO/FIXME no código (não em comentários)
```
pattern_search(pattern='$VAR = "TODO"', language='python')
```
Para comentários, use grep, o pattern_search casa estrutura de código, não comentários.

### Quando usar pattern_search vs. grep
- **pattern_search**: padrões estruturais de código (assinaturas de função, error handling, chamadas de API)
- **grep**: texto literal, comentários, valores de config, mensagens de log

## Padrões de diagnóstico multi-componente

### Instrumentação de borda

Quando o sistema tem múltiplos componentes, adicione logging de diagnóstico em cada borda:

```bash
# Layer 1: Workflow
echo "=== Secrets available in workflow: ==="
echo "IDENTITY: ${IDENTITY:+SET}${IDENTITY:-UNSET}"

# Layer 2: Build script
echo "=== Env vars in build script: ==="
env | grep IDENTITY || echo "IDENTITY not in environment"

# Layer 3: Signing script
echo "=== Keychain state: ==="
security list-keychains
security find-identity -v

# Layer 4: Actual signing
codesign --sign "$IDENTITY" --verbose=4 "$APP"
```

Isso revela qual layer falha (secrets → workflow ✓, workflow → build ✗).

### Backward Tracing

Quando o erro está fundo no call stack:
1. Comece pelo erro
2. Use `goto_definition` para navegar até a função
3. Use `find_references` para encontrar todos os callers
4. Rastreie para trás: quem chamou isso com dados ruins?
5. Continue indo até encontrar a origem
6. Corrija na origem, não no sintoma

### Espera baseada em condição

Substitua timeouts arbitrários por polling de condição:
```bash
# Bad: sleep 30
# Good:
for i in $(seq 1 60); do
  curl -s http://localhost:8080/health && break
  sleep 1
done
```

### Localização de regressão por Git Bisect

Use quando um bug é uma **regressão**, algo que antes funcionava e agora não.

**Quando usar:**
- Você consegue identificar um commit "good" (onde funcionava) e um commit "bad" (onde está quebrado)
- O bug é reproduzível com um teste ou check manual

**Fluxo:**
```bash
# 1. Start bisect
git log --oneline -20  # find good/bad commit range
git bisect start
git bisect bad HEAD    # current commit is broken
git bisect good <known-good-sha>

# 2. Automated mode (preferred — if you have a test)
git bisect run <test-command>
# e.g.: git bisect run pytest tests/test_auth.py::test_login -x

# 3. Manual mode (if no automated test)
# At each step, git checks out a commit. Test it, then:
git bisect good  # if this commit works
git bisect bad   # if this commit is broken

# 4. When done — git reports the first bad commit
git bisect reset  # return to original branch
```

**Após encontrar o commit culpado:**
1. Leia o diff completo: `git show <culprit-sha>`
2. Entenda o que mudou e por que isso quebrou o comportamento
3. Isso restringe a causa raiz de "em algum lugar da codebase" para "essa mudança específica".

**Análise semântica assistida por LLM:**
Para cada diff de step do bisect, analise se as alterações são semanticamente relacionadas ao comportamento alvo. Isso ajuda quando o predicate é ruidoso (testes flaky, comportamento não determinístico). Foque em: transições de estado, mudanças de error handling e modificações de dependência.
