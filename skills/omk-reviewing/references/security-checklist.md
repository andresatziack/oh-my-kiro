# Checklist de Segurança e Confiabilidade

## Input/Output Safety

- **XSS**: injeção de HTML insegura, `dangerouslySetInnerHTML`, templates sem escape, atribuições a innerHTML
- **Injection**: SQL/NoSQL/command/GraphQL injection via concatenação de strings ou template literals
- **SSRF**: URLs controladas pelo usuário alcançando serviços internos sem allowlist
- **Path traversal**: input do usuário em paths de arquivo sem sanitização (ataques `../`)
- **Prototype pollution**: merge inseguro de objetos em JavaScript (`Object.assign`, spread com input do usuário)

## AuthN/AuthZ

- Falta de checks de tenant ou ownership em operações de read/write
- Novos endpoints sem auth guards ou enforcement de RBAC
- Confiar em roles/flags/IDs vindos do client
- Broken access control (IDOR, Insecure Direct Object Reference)
- Session fixation ou gerenciamento de sessão fraco

## JWT e segurança de tokens

- Algorithm confusion (aceitar `none` ou `HS256` quando esperado `RS256`)
- Secrets fracos ou hardcoded
- Sem expiração (`exp`) ou sem validação dela
- Dados sensíveis no payload do JWT (tokens são base64, não criptografados)
- Não validar `iss` (issuer) ou `aud` (audience)

## Secrets e PII

- API keys, tokens ou credenciais em código/config/logs
- Secrets no histórico do git ou em env vars expostas para o client
- Logging excessivo de PII ou payloads sensíveis
- Falta de mascaramento de dados em mensagens de erro

## Supply Chain e dependências

- Dependências sem pinning, permitindo updates maliciosos
- Dependency confusion (colisão de nome com pacote privado)
- Importação de fontes ou CDNs não confiáveis sem checks de integridade
- Dependências desatualizadas com CVEs conhecidos

## CORS e Headers

- CORS muito permissivo (`Access-Control-Allow-Origin: *` com credentials)
- Falta de security headers (CSP, X-Frame-Options, X-Content-Type-Options)
- Headers internos ou stack traces expostos

## Riscos de runtime

- Loops sem limite, chamadas recursivas ou buffers grandes em memória
- Falta de timeouts, retries ou rate limiting em chamadas externas
- Operações bloqueantes no path da request (sync I/O em contexto async)
- Esgotamento de recursos (file handles, conexões, memória)
- ReDoS (Regular Expression Denial of Service)

## Criptografia

- Algoritmos fracos (MD5, SHA1 para fins de segurança)
- IVs ou salts hardcoded
- Usar criptografia sem autenticação (modo ECB, sem HMAC)
- Comprimento de chave insuficiente

## Race Conditions

Race conditions são bugs sutis que causam falhas intermitentes e vulnerabilidades de segurança. Atenção especial a:

### Acesso a estado compartilhado
- Múltiplas threads/goroutines/tasks async acessando variáveis compartilhadas sem sincronização
- Estado global ou singletons modificados concorrentemente
- Inicialização lazy sem locking adequado (issues de double-checked locking)
- Coleções não thread-safe usadas em contexto concorrente

### Check-Then-Act (TOCTOU)
- Padrões `if (exists) then use` sem operações atômicas
- `if (authorized) then perform` em que a autorização pode mudar
- Check de existência de arquivo seguido de operação no arquivo
- Check de saldo seguido de débito (operações financeiras)
- Check de inventário seguido de criação de pedido

### Concorrência em banco de dados
- Falta de optimistic locking (coluna `version`, checks em `updated_at`)
- Falta de pessimistic locking (`SELECT FOR UPDATE`)
- Read-modify-write sem isolamento de transação
- Incrementos de contador sem operações atômicas (`UPDATE SET count = count + 1`)
- Violações de unique constraint em inserts concorrentes

### Sistemas distribuídos
- Falta de distributed locks para recursos compartilhados
- Race conditions em leader election
- Races de invalidação de cache (leituras stale após writes)
- Dependências de ordem de eventos sem sequenciamento adequado
- Cenários de split-brain em operações de cluster

### Padrões comuns para sinalizar
```
# Dangerous patterns:
if not exists(key):       # TOCTOU
    create(key)

value = get(key)          # Read-modify-write
value += 1
set(key, value)

if user.balance >= amount:  # Check-then-act
    user.balance -= amount
```

### Perguntas a fazer
- "What happens if two requests hit this code simultaneously?"
- "Is this operation atomic or can it be interrupted?"
- "What shared state does this code access?"
- "How does this behave under high concurrency?"

## Integridade de dados

- Falta de transações, writes parciais ou updates de estado inconsistentes
- Validação fraca antes da persistência (issues de coerção de tipo)
- Falta de idempotência em operações com retry
- Lost updates por modificações concorrentes
