---
name: omk-coding
description: "Enforces coding best practices: deep-read before modify, LSP-first navigation, TDD red-green-refactor, minimal changes, self-review, verification. Trigger when writing code, modifying source files, fixing bugs, refactoring, optimizing code, entering a worktree or submodule, or when user says 'write code', 'implement', 'fix this', 'fix PR', 'add feature', 'add field', 'refactor', 'optimize', 'modify', 'change this', 'update code', 'apply feedback', 'apply review', '改代码', '修复', '加个', '改一下', '优化'. Also trigger when creating/editing .java .py .ts .js .go .rs .sh .tsx .jsx .vue .css .scss files, or after debugging identifies root cause and implementation begins."
---

# Coding - Escrever código do jeito certo

## Trigger Examples
- "帮我实现这个功能"
- "fix this bug in the auth module"
- "重构一下这段代码"
- "修复 PR review 发现的问题"
- "改一下这个 hook 的逻辑"
- "apply the review feedback"
- "优化这段代码的性能"
- "加个字段到这个 model 里"

## Visão geral

Escrever código sem disciplina cria dívida. Esta skill aplica qualidade no ponto de criação.

**Princípio central:** Toda alteração de código deve ser mínima, testada, verificada e auto-revisada antes de ser declarada pronta.

## Phase 0: Preparação do ambiente

Antes de escrever qualquer código em uma worktree ou submodule:

```
1. Initialize LSP for semantic analysis:
   /code init

2. Get project overview:
   generate_codebase_overview

3. Detect language & build system:
   - Java → find pom.xml / build.gradle → note test command (mvn test / gradle test)
   - TypeScript/JS → find package.json → note test command (npm test / vitest / jest)
   - Python → find pyproject.toml / pytest.ini → note test command (pytest)
   - Rust → Cargo.toml → cargo test
   - Go → go test ./...

4. Run existing tests to establish baseline:
   <detected test command>
   Record: N tests, M passing, K failing
```

**Se a inicialização do LSP falhar:** Tente novamente com `/code init -f`. Se ainda falhar, registre em Errors do plan e continue com fallback de grep, mas observe a qualidade degradada da análise.

## Phase 0.5: Deep Read - Construir entendimento (OBRIGATÓRIO)

> **Esta phase NÃO é opcional.** Mesmo para alterações "simples", você DEVE concluí-la antes de escrever qualquer código.
> A pesquisa mostra: o modo de falha mais caro é código que está "correto isoladamente, mas quebra o sistema ao redor" (Boris Tane). Agents só exploram dependências em 42% das vezes quando deixados decidir por conta própria (CodeCompass). Esta phase força os outros 58%.

```
1. goto_definition — navigate to the code you'll change, read it deeply (not skim)

2. find_references — map ALL callers and dependents of the symbols you'll modify
   Output: list of files and functions that call/use the target code

3. get_document_symbols — understand the internal structure of files you'll modify
   Output: key types, functions, constants in each file

4. Read adjacent code — other files in the same module/package
   Look for: naming conventions, error handling patterns, test patterns, shared utilities

5. get_diagnostics — record current state (zero new errors allowed after your change)

6. Synthesize a Codebase Understanding summary (output this explicitly):

   Codebase Understanding:
   - Module role: [what this module does in the system]
   - File structure: [key symbols in the files you'll modify]
   - Callers: [who calls the code you'll modify]
   - Dependencies: [what the target code depends on]
   - Conventions: [code style, naming, error handling patterns]
   - Impact scope: [which other files/modules could be affected by your change]

7. Signal completion:
   touch /tmp/omk-coding-deep-read-done
```

**Se você não conseguir responder a algum campo do resumo de Codebase Understanding**, você não leu código suficiente. Volte e leia mais antes de prosseguir.

## Phase 1: Entender antes de alterar

Antes de modificar qualquer arquivo, confirme que você concluiu a Phase 0.5 e que seu Codebase Understanding cobre o código alvo.

**Regras (Iron Rules, sem exceções):**
- Sem modificação sem goto_definition
- Sem refactor sem find_references
- Sem nova API pública sem buscar abstrações similares já existentes
- Siga o estilo de código existente, não introduza convenções novas

## Phase 2: Escrever código (TDD)

### Red → Green → Refactor

```
Step 1: Write failing test FIRST
  - Test names: methodName_condition_expectedResult
  - One behavior per test
  - Run test → must FAIL (red)

Step 2: Write minimal implementation
  - Solve ONLY what the test requires
  - No speculative features (YAGNI)
  - No premature abstraction

Step 3: Run test → must PASS (green)

Step 4: Refactor if needed
  - Extract only when duplication is real (not imagined)
  - Run tests again → still PASS
```

### Regras de alteração mínima

| Regra | Verificação |
|------|-------|
| Single responsibility | Esta alteração faz exatamente uma coisa? |
| Minimal diff | Alguma linha pode ser removida sem quebrar o objetivo? |
| Sem drive-by fixes | Melhorias não relacionadas vão em commits separados |
| Sem novas dependências | A menos que essenciais e aprovadas |
| Backward compatible | Callers existentes não afetados, exceto quando intencional |
| **Match existing style** | Siga as convenções do código ao redor, não o seu ideal. Se a codebase está em 85/100, escreva código 85 a 90/100, não persiga 100 |
| **Don't "fix" old code** | Código existente funciona. Não refatore, não restilize, não "melhore" código fora do escopo da sua alteração. Se ver um problema real, registre separadamente |

### Gates de qualidade de código

- Métodos ≤ 20 linhas (divida quando maiores)
- Sem parâmetros booleanos de flag, divida em dois métodos
- Sem exceções engolidas, o catch deve logar ou rethrow
- Retorne coleções vazias, não null
- Use nomes auto-explicativos, comentários explicam o PORQUÊ, não o QUÊ
- Dependa de interfaces, não de implementações concretas

## Phase 3: Auto-verify

Após a implementação, antes de declarar pronto:

```
1. Run full test suite (not just new tests):
   <project test command>
   → Must show 0 new failures

2. Run linter/compiler:
   get_diagnostics on all modified files
   → Must show 0 new errors/warnings

3. Check diff scope:
   git diff --stat
   → Every changed file must be intentional

4. Regression check:
   - New test passes? → Revert your fix → test must FAIL → restore fix
   - This proves the test actually tests your change
```

### Verificação visual de frontend (quando arquivos de UI mudaram)

Se algum arquivo modificado for de frontend (.tsx/.jsx/.vue/.html/.css/.scss), você DEVE verificar visualmente:

```
1. Ensure dev server is running (check with curl or ps)
2. Use agent-browser to screenshot the affected page:
   agent-browser open http://localhost:<port>/<path> && agent-browser wait --load networkidle && agent-browser screenshot --annotate
3. Review the screenshot — does it match the expected behavior?
4. If the visual result is wrong, fix and re-verify. Do NOT claim done without visual confirmation.
5. For style/layout issues, use agent-browser snapshot -i to inspect element structure
```

**CRÍTICO:** Nunca declare que um problema de frontend está "fixed" baseado apenas em alterações de código. O browser é a fonte da verdade.

## Phase 4: Auto-review

Antes de commitar, revise seu próprio diff:

```
1. git diff (staged or unstaged)

2. For each changed file, check:
   □ SRP — one reason to change?
   □ No dead code introduced
   □ Error paths handled (what if this fails?)
   □ Boundary conditions (null, empty, zero, max)
   □ No hardcoded values — use constants/config
   □ Thread safety (if concurrent context)

3. Ask yourself:
   - "What breaks if I revert this?"
   - "What breaks if input is unexpected?"
   - "Would a new team member understand this?"
```

**Se alguma verificação falhar:** Corrija antes de commitar. Não deixe TODOs para "depois".

## Phase 4.5: Auto-explicação

Após o auto-review, explique suas alterações em linguagem natural antes de commitar:

```
1. What did I change and why?
2. How do my changes interact with the callers/dependencies identified in Phase 0.5 (Codebase Understanding)?
3. Are there potential side effects on other modules?
```

**Se você descobrir uma contradição lógica enquanto explica** → volte para a Phase 2 e revisite a implementação. O ato de explicar costuma revelar erros que o code review não pega (pesquisa de Self-Debugging: explicação supera chain-of-thought na detecção de erros).

## Phase 5: Commit

```bash
# Verify one last time
<test command>

# Commit with descriptive message
git add -p  # stage intentionally, not git add .
git commit -m "<type>: <what changed and why>"
```

Tipos de commit message: `feat`, `fix`, `refactor`, `test`, `docs`, `chore`

## Adendos por linguagem

### Java
- Carregue `knowledge/reference/java-coding-standards.md` ao mexer em arquivos .java
- Após mudanças em interfaces: `mvn compile -pl <module> -am`
- Após todas as alterações: `mvn clean test`
- Prefira injeção via construtor a @Autowired

### TypeScript/JavaScript
- Modo strict, sem `any` salvo justificado
- Prefira `const` a `let`, nunca `var`
- Trate erros async, sem promise rejections não tratadas

### Python
- Type hints em todas as funções públicas
- `pytest` com flag `-v` para visibilidade
- Sem `except:` cru, sempre especifique o tipo de exceção

## Quando aplicar

**Sempre quando:**
- Criando novos arquivos em uma worktree/submodule
- Modificando código existente
- Corrigindo bugs (TDD: escreva primeiro um teste falhando que reproduza o bug)
- Refatorando

**Pule a Phase 2 (TDD) somente quando:**
- Alterações puramente de documentação
- Alterações somente de config (ainda assim, verifique)
- O usuário disser explicitamente "skip tests"

## Anti-padrões

| Não faça | Faça em vez disso |
|-------|-----------|
| Escrever código e "adicionar testes depois" | Teste primeiro, sempre |
| `git add .` | `git add -p`, faça stage de forma intencional |
| Fix + cleanup não relacionado no mesmo commit | Commits separados |
| Confiar em "deveria funcionar" | Rode e veja a saída |
| Copy-paste sem entender | Leia o source e adapte |
| Adicionar abstração "para uso futuro" | Resolva o problema de hoje |
