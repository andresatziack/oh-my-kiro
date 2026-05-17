# Checklist de Qualidade de Código

## Tratamento de erros

### Anti-padrões para sinalizar

- **Exceções engolidas**: blocos catch vazios ou catch só com log
  ```javascript
  try { ... } catch (e) { }  // Silent failure
  try { ... } catch (e) { console.log(e) }  // Log and forget
  ```
- **Catch muito amplo**: capturar a base `Exception`/`Error` em vez de tipos específicos
- **Vazamento de informação no erro**: stack traces ou detalhes internos expostos a usuários
- **Falta de tratamento de erro**: sem try-catch ao redor de operações falíveis (I/O, network, parsing)
- **Async error handling**: promise rejections não tratadas, falta de `.catch()`, sem error boundary

### Boas práticas a verificar

- [ ] Erros são capturados em fronteiras apropriadas
- [ ] Mensagens de erro são amigáveis ao usuário (sem detalhes internos expostos)
- [ ] Erros são logados com contexto suficiente para depuração
- [ ] Erros async são propagados ou tratados corretamente
- [ ] Comportamento de fallback está definido para erros recuperáveis
- [ ] Erros críticos disparam alertas/monitoramento

### Perguntas a fazer
- "What happens when this operation fails?"
- "Will the caller know something went wrong?"
- "Is there enough context to debug this error?"

---

## Performance e Caching

### Operações CPU-intensivas

- **Operações caras em hot paths**: compilação de regex, parsing de JSON, crypto em loops
- **Bloqueio da main thread**: sync I/O, computação pesada sem worker/async
- **Recomputação desnecessária**: mesma conta feita múltiplas vezes
- **Falta de memoização**: funções puras chamadas repetidamente com os mesmos inputs

### Banco de dados e I/O

- **N+1 queries**: loop que faz uma query por item em vez de batch
  ```javascript
  // Bad: N+1
  for (const id of ids) {
    const user = await db.query(`SELECT * FROM users WHERE id = ?`, id)
  }
  // Good: Batch
  const users = await db.query(`SELECT * FROM users WHERE id IN (?)`, ids)
  ```
- **Falta de índices**: queries em colunas sem índice
- **Over-fetching**: SELECT * quando apenas algumas colunas são necessárias
- **Sem paginação**: carregar dataset inteiro em memória

### Issues de cache

- **Falta de cache em operações caras**: chamadas de API repetidas, queries de DB, computações
- **Cache sem TTL**: dados stale servidos indefinidamente
- **Cache sem estratégia de invalidação**: dados atualizados mas cache não limpo
- **Colisões de cache key**: unicidade de key insuficiente
- **Cachear dados específicos do usuário globalmente**: issue de segurança/privacidade

### Memória

- **Coleções sem limite**: arrays/maps que crescem sem cap
- **Retenção de objetos grandes**: manter referências impedindo GC
- **Concatenação de strings em loops**: use StringBuilder/join
- **Carregar arquivos grandes inteiros**: use streaming

### Perguntas a fazer
- "What's the time complexity of this operation?"
- "How does this behave with 10x/100x data?"
- "Is this result cacheable? Should it be?"
- "Can this be batched instead of one-by-one?"

---

## Condições de borda

### Tratamento de Null/Undefined

- **Falta de checks de null**: acessar propriedades em objetos potencialmente null
- **Confusão truthy/falsy**: `if (value)` quando `0` ou `""` são válidos
- **Optional chaining em excesso**: `a?.b?.c?.d` escondendo problemas estruturais
- **Inconsistência null vs. undefined**: uso misturado sem convenção clara

### Coleções vazias

- **Array vazio não tratado**: o código assume que o array tem itens
- **Edge case de objeto vazio**: `for...in` ou `Object.keys` em objeto vazio
- **Acesso a primeiro/último elemento**: `arr[0]` ou `arr[arr.length-1]` sem check de length

### Limites numéricos

- **Divisão por zero**: falta de check antes da divisão
- **Integer overflow**: números grandes excedendo o safe integer range
- **Comparação de ponto flutuante**: usar `===` em vez de comparação por epsilon
- **Valores negativos**: índice ou contagem que não deveria ser negativo
- **Off-by-one**: bounds de loop, slicing de array, paginação

### Limites de string

- **String vazia**: não tratada como edge case
- **String só de whitespace**: passa no truthy check, mas é efetivamente vazia
- **Strings muito longas**: sem limites de tamanho, causando issues de memória/exibição
- **Edge cases Unicode**: emoji, texto RTL, combining characters

### Padrões comuns para sinalizar

```javascript
// Dangerous: no null check
const name = user.profile.name

// Dangerous: array access without check
const first = items[0]

// Dangerous: division without check
const avg = total / count

// Dangerous: truthy check excludes valid values
if (value) { ... }  // fails for 0, "", false
```

### Perguntas a fazer
- "What if this is null/undefined?"
- "What if this collection is empty?"
- "What's the valid range for this number?"
- "What happens at the boundaries (0, -1, MAX_INT)?"
