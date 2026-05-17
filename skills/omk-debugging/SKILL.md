---
name: omk-debugging
description: "Systematic debugging: reproduce → hypothesize → verify → fix. Trigger when encountering bugs, test failures, errors, crashes, unexpected behavior, or when user says 'debug', 'not working', 'broken', 'fails', 'error', 'exception', 'why does this happen', 'investigate'. Also trigger on stack traces, error logs, or non-zero exit codes."
---

## Trigger Examples
- "esse teste nao passa"
- "why is this returning null?"
- "deu erro, da uma olhada pra mim"
- "build fails with exit code 1"
- "investigate why the hook isn't firing"

# Depuração sistemática

## Visão geral

Fixes aleatórios desperdiçam tempo e criam bugs novos. Patches rápidos mascaram problemas subjacentes.

**Princípio central:** SEMPRE encontre a causa raiz antes de tentar fixes. Fixes de sintoma são falha.

**Violar a letra deste processo é violar o espírito da depuração.**

## A Lei de Ferro

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

Se você não concluiu a Phase 1, não pode propor fixes.

### Três Leis de Ferro do Code Debugging

1. **Sem goto_definition = sem modificar**, não altere código que você não navegou até a definição
2. **Sem find_references = sem refactor**, não refatore sem conhecer todos os locais de uso
3. **Sem get_diagnostics = sem reivindicar fix**, não declare um fix sem verificar zero novos diagnostics

## Protocolo do documento de investigação

O documento de investigação (`docs/investigations/{date}-{topic}.md`) é o registro persistente e inter-sessão de um esforço de depuração. Crie um no início de toda sessão de debug não trivial usando `skills/omk-debugging/investigation-template.md`.

### Sistema de evidências em três níveis

| Nível | Rótulo | Significado | Mutabilidade |
|-------|-------|---------|------------|
| 🔒 L0 | Machine Facts | Saída de comando, análise de código, respostas de API, resultados de experimento | **Imutável**, só pode ser sobreposto por evidência L0 mais forte |
| 👤 L1 | Human Observations | Operações e fenômenos reportados pelo usuário | **Protegido**, precisa de evidência L0 + justificativa documentada para ser contestado |
| 🤖 L2 | Agent Inferences | Deduções de IA, hipóteses, conclusões de análise | **Mutável**, pode ser revisado livremente, marque a entrada antiga ~~struck~~ e mantenha o original |


### Regras de atualização por seção

| Seção | Modo de atualização | Regra |
|---------|-------------|------|
| Status Overview | **Sobrescrever** | Atualize após cada conclusão de Stage, deve refletir o estado atual o tempo todo |
| Evidence Table | **Append-only** | Nunca delete ou edite entradas existentes, apenas adicione novas linhas |
| Investigation Tree | **Sobrescrever** | Atualize status dos ramos (⬜→✅/❌) conforme a investigação avança |
| Decision Log | **Append-only** | Decisões superseded permanecem, marque o status como "❌ substituida por D{n}" |
| Experiment Log | **Append-only** | Cada experimento recebe um ID único EXP-{n} para referência cruzada |
| Ruled Out | **Append-only** | Direções eliminadas permanecem permanentemente para evitar reinvestigação |
| Timeline | **Append-only** | Marcos cronológicos, nunca reescritos |

## Regras antirregressão

Estas regras impedem que novas sessões desfaçam o progresso prévio da investigação:

1. **Para sobrepor fatos 🔒 L0**: Requer evidência L0 mais forte (nova saída de comando ou experimento). É preciso registrar evidência antiga e nova na Evidence Table com comparação explícita.
2. **Para contestar observações 👤 L1**: Requer evidência L0 que contradiga a observação. É preciso documentar a justificativa do questionamento na Timeline.
3. **Para revisar inferências 🤖 L2**: Livre para revisar. Marque a inferência antiga ~~struck~~ (não delete). A nova inferência deve indicar "substitui I{n}".
4. **Decision Log**: Decisões rejeitadas devem incluir justificativa de rejeição. Novas sessões NÃO devem retentar uma abordagem rejeitada, exceto se nova evidência L0 invalidar o motivo da rejeição.
5. **Ruled Out**: Direções de investigação eliminadas NÃO devem ser reinvestigadas, exceto se surgir nova evidência L0 não disponível quando a direção foi descartada.

## Matriz de decisão de tools

| Tipo de bug | Sequência de tools | Por quê |
|----------|--------------|-----|
| Erro de compilação/tipo | `get_diagnostics` → `goto_definition` → `get_hover` | Diagnostics apontam o erro, definição mostra contexto, hover revela tipos |
| Comportamento errado | `search_symbols` → `find_references` → `goto_definition` | Encontre o símbolo, rastreie todos os callers, leia a implementação |
| Codebase desconhecida | `get_document_symbols` → `goto_definition` → `get_hover` | Mapeia estrutura do arquivo, navega até definições, entende tipos |
| Refactor quebrou algo | `find_references` → `get_diagnostics` → `search_symbols` | Encontre todos os usos, verifique novos erros, localize símbolos relacionados |
| Falha de teste | `get_diagnostics` → `search_symbols` → `find_references` | Verifique erros de compilador primeiro, encontre o sujeito do teste, rastreie dependências |

**Quando usar grep em vez disso:** Apenas para buscar comentários, string literals, valores de config ou arquivos não-código.

## Quando usar

Use para QUALQUER problema técnico:
- Falhas de teste
- Bugs em produção
- Comportamento inesperado
- Problemas de performance
- Falhas de build
- Problemas de integração

**Use isto ESPECIALMENTE quando:**
- Sob pressão de tempo (emergências tornam o "chute" tentador)
- "Just one quick fix" parece óbvio
- Você já tentou vários fixes
- O fix anterior não funcionou
- Você não entende totalmente o problema

**Não pule quando:**
- O problema parece simples (bugs simples também têm causa raiz)
- Você está com pressa (correr garante retrabalho)
- O gerente quer o fix AGORA (sistemático é mais rápido que ficar batendo cabeça)

## As Quatro Phases

Você DEVE concluir cada phase antes de prosseguir para a próxima.

### Phase 1: Investigação da causa raiz

**ANTES de tentar QUALQUER fix:**

**Step -1: Construa o Architectural Context (OBRIGATÓRIO, NÃO pule)**

Antes de olhar para qualquer código específico, construa um mapa do sistema ao redor do bug. Esse step resolve o problema de "structural blindness", LLMs processam código como texto e não conseguem ver grafos de dependência, cadeias de chamada ou fronteiras arquiteturais sem navegação explícita.

1. Rode `generate_codebase_overview` para obter a estrutura de módulos de alto nível do projeto
2. Para o(s) símbolo(s) central(is) do bug, rode `find_references` para descobrir todos os callers e locais de uso
3. Para o(s) arquivo(s) do bug, rode `get_document_symbols` para entender a estrutura interna
4. Produza um resumo de **Architectural Context**:

```
Architectural Context:
- Module: [where this code sits in the system architecture]
- Upstream callers: [who calls the buggy code — list file:function]
- Downstream dependencies: [what the buggy code depends on]
- Cross-module impact: [which other modules could be affected by a fix]
- Hidden dependencies: [files with no semantic overlap but architectural connection]
```

Por que isso é obrigatório: a pesquisa CodeCompass (258 trials) mostrou que a navegação por grafo de dependências alcança 99,4% de cobertura arquitetural em hidden dependencies, contra 76,2% sem ela (+23,2pp). Agents só exploram dependências espontaneamente em 42% das vezes, quando pulam, a performance iguala a da baseline sem tools. Esse step precisa ser forçado, não opcional.

**Step 0: Verifique episodes passados**
- Leia `knowledge/episodes.md` em busca de bugs passados similares
- Erros do passado costumam se repetir, verifique antes de investigar do zero

**Step 0.5: Classifique o tipo de falha (Failure Classification)**

Antes de mergulhar na investigação, classifique a falha para guiar sua abordagem. Escolha a categoria mais provável:

| Categoria | Descrição | Sinal típico |
|----------|-------------|----------------|
| Logic/Semantic Error | A lógica do código está errada | Teste falha, saída errada |
| Environment/Config Error | Problema de ambiente, config ou dependência | Funciona local, falha em CI |
| Concurrency/Timing Error | Race condition, dependência de timing | Falha intermitente |
| Invalid Invocation | Chamada de tool/API malformada ou sem args | Erro de schema, resposta 400 |
| Misinterpretation of Output | Agiu sobre uma suposição errada de retorno | Lógica downstream errada |
| Intent–Plan Misalignment | Resolvendo o problema errado | O fix não trata o problema real do usuário |
| Plan Adherence Failure | Pulou steps obrigatórios ou fez ações fora do plan | Step esperado não executado |
| Invention of New Information | Alucinou dados que não estão no trace/saída de tool | Refere variável/arquivo inexistente |
| Under-specified Intent | Sem informação suficiente para prosseguir | Precisa de mais contexto do usuário |

Escreva sua classificação na Diagnostic Evidence (Step 6). Em caso de dúvida, escolha os 2 candidatos principais e investigue ambos.

**Step 1: Rode get_diagnostics primeiro**
- Rode `get_diagnostics` no(s) arquivo(s) com falha para obter erros, warnings e hints do compilador
- Isso dá os locais e tipos exatos do erro, muito mais preciso do que ler logs

**Step 2: Use search_symbols para encontrar o código relevante**
- Use `search_symbols` para localizar a função/classe/variável envolvida no erro
- Em seguida, use `goto_definition` para ler a implementação real
- Use `find_references` para entender todos os callers e locais de uso

**Step 3: Leia mensagens de erro com atenção**
- Não pule erros ou warnings
- Eles costumam conter a solução exata
- Leia stack traces por completo
- Anote números de linha, paths de arquivo, códigos de erro

**Step 4: Reproduza de forma consistente**
- Você consegue disparar o bug de forma confiável?
- Quais são os steps exatos?
- Acontece todas as vezes?
- Se não for reproduzível → colete mais dados, não chute

**Step 5: Verifique alterações recentes**
- O que mudou que poderia causar isso?
- Git diff, commits recentes
- Novas dependências, mudanças de config
- Diferenças de ambiente
- **Se for uma regressão** (antes funcionava e agora não): use o fluxo de Git Bisect em `reference.md` para localizar o commit exato que introduziu o bug

**Step 6: Reúna a Diagnostic Evidence**

Você DEVE produzir um resumo de **Diagnostic Evidence** antes de ir para a Phase 2:

```
Diagnostic Evidence:
- failure_type: [category from Step 0.5 classification]
- get_diagnostics: [what errors/warnings were found]
- search_symbols: [what symbols were located]
- find_references: [what callers/usage sites were found]
- get_hover: [what type information was revealed]
- key_variables:
  - var_name: [variable name]
    expected: [expected value at this point]
    actual: [actual value observed]
    location: [file:line where divergence occurs]
  - ...
- Root cause hypothesis: [your conclusion based on above]
```

Sem essa evidência, você não pode prosseguir.

**Step 7: Reúna evidência em sistemas multi-componente**

QUANDO o sistema tiver múltiplos componentes (CI → build → signing, API → service → database):

ANTES de propor fixes, adicione instrumentação de diagnóstico:
```
For EACH component boundary:
  - Log what data enters component
  - Log what data exits component
  - Verify environment/config propagation
  - Check state at each layer

Run once to gather evidence showing WHERE it breaks
THEN analyze evidence to identify failing component
THEN investigate that specific component
```

**Step 8: Rastreie o fluxo de dados**

QUANDO o erro estiver fundo no call stack:
- Use `goto_definition` para navegar até a origem do erro
- Use `find_references` para rastrear callers para trás
- De onde origina o valor ruim?
- Continue rastreando para cima até encontrar a origem
- Corrija na origem, não no sintoma

### Phase 2: Análise de padrões

**Encontre o padrão antes de corrigir:**

1. **Encontre exemplos funcionais**
   - Localize código semelhante e funcional na mesma codebase
   - Use `search_symbols` para encontrar padrões similares
   - O que funciona que é parecido com o que está quebrado?

2. **Compare com referências**
   - Se for implementar um padrão, leia a implementação de referência POR INTEIRO
   - Não passe os olhos, leia cada linha
   - Entenda o padrão totalmente antes de aplicar

3. **Identifique diferenças**
   - O que é diferente entre o que funciona e o que está quebrado?
   - Liste cada diferença, por menor que seja
   - Não assuma "isso não pode importar"

4. **Entenda dependências**
   - De que outros componentes isso precisa?
   - Quais settings, configs, ambiente?
   - Quais suposições faz?

### Phase 3: Hipótese e teste

**Método científico:**

1. **Forme uma hipótese única**
   - Declare claramente: "I think X is the root cause because Y"
   - Anote
   - Seja específico, não vago

2. **Teste de forma mínima**
   - Faça a MENOR alteração possível para testar a hipótese
   - Uma variável de cada vez
   - Não conserte várias coisas ao mesmo tempo

3. **Verifique antes de continuar**
   - Funcionou? Sim → Phase 4
   - Não funcionou? Forme uma NOVA hipótese
   - NÃO empilhe mais fixes em cima

4. **Quando você não souber**
   - Diga "I don't understand X"
   - Não finja saber
   - Peça ajuda
   - Pesquise mais

### Phase 4: Implementação

**Corrija a causa raiz, não o sintoma:**

1. **Rode get_diagnostics antes do fix (baseline)**
   - Registre a contagem atual de diagnostics e detalhes
   - Esse é o snapshot "antes"

2. **Crie um caso de teste que falha**
   - A reprodução mais simples possível
   - Teste automatizado, se possível
   - DEVE existir antes de corrigir

3. **Implemente um único fix**
   - Endereça a causa raiz identificada
   - UMA alteração por vez
   - Sem melhorias do tipo "while I'm here"
   - Sem refactor empacotado

4. **Rode get_diagnostics após o fix (verify)**
   - Compare com a baseline: novos diagnostics devem ser 0
   - Todos os diagnostics originais devem estar resolvidos ou inalterados
   - Se aparecerem novos diagnostics, seu fix introduziu problemas, reverta

5. **Verifique o fix**
   - O teste passa agora?
   - Outros testes ficaram quebrados?
   - O issue está realmente resolvido?

5.5. **Auto-explicação (Verificação tipo Rubber Duck)**
   Após verificar que o fix funciona, explique em linguagem natural:
   - **Causa raiz**: O que estava errado exatamente e por quê?
   - **Lógica do fix**: Por que esse fix resolve a causa raiz?
   - **Efeitos colaterais**: Esse fix pode introduzir novos problemas? Verifique contra o Architectural Context do Step -1.

   Se você descobrir uma contradição lógica enquanto explica → PARE, volte à Phase 3 e re-verifique sua hipótese. O ato de explicar costuma revelar raciocínio falho que o teste sozinho não pega.

6. **Se o fix não funcionar**
   - PARE
   - Conte: quantos fixes você já tentou?
   - Se < 3: volte à Phase 1 e reanalise com a nova informação
   - **Se ≥ 3: PARE e questione a arquitetura (step 7 abaixo)**
   - NÃO tente o Fix #4 sem discussão arquitetural

7. **Se 3+ fixes falharem: questione a arquitetura**

   **Padrão indicando problema arquitetural:**
   - Cada fix revela novo shared state/coupling/problema em outro lugar
   - Fixes exigem "massive refactoring" para serem implementados
   - Cada fix cria sintomas novos em outro lugar

   **PARE e questione fundamentos:**
   - Esse padrão é fundamentalmente sólido?
   - Estamos "sticking with it through sheer inertia"?
   - Devemos refatorar a arquitetura em vez de continuar corrigindo sintomas?

   **Discuta com seu human partner antes de tentar mais fixes**

8. **Pós-fix Review**
   Depois de o fix estar verificado e funcionando:
   - Compare o código original com bug vs. o código corrigido, o fix está mínimo?
   - Verifique: o fix introduziu code smells (duplicação, magic numbers, falta de error handling)?
   - Verifique: o fix precisa de programação defensiva em outros call sites? (Consulte o Architectural Context do Step -1)
   - Escreva um resumo de uma linha em `knowledge/episodes.md`, se for um padrão de bug novo
   - Atualize o documento de investigação: defina **Status Overview** como 🟢 Resolved, registre causa raiz final e fix no **Decision Log**

## Sinais de alerta - PARE e siga o processo

Se você se pegar pensando:
- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- "Add multiple changes, run tests"
- "Skip the test, I'll manually verify"
- "It's probably X, let me fix that"
- "I don't fully understand but this might work"
- "Pattern says X but I'll adapt it differently"
- "Here are the main problems: [lists fixes without investigation]"
- Propondo soluções antes de rastrear o fluxo de dados
- **"One more fix attempt" (quando já tentou 2+)**
- **Cada fix revela um problema novo em outro lugar**
- **Usando grep para encontrar código em vez de search_symbols/find_references**

**TODOS esses significam: PARE. Volte para a Phase 1.**

**Se 3+ fixes falharem:** Questione a arquitetura (veja Phase 4.7)

## Sinais do seu human partner de que você está fazendo errado

**Atenção a estas redirections:**
- "Is that not happening?", você assumiu sem verificar
- "Will it show us...?", você devia ter adicionado coleta de evidência
- "Stop guessing", você está propondo fixes sem entender
- "Ultrathink this", questione fundamentos, não só sintomas
- "We're stuck?" (frustrado), sua abordagem não está funcionando

**Quando ver estes:** PARE. Volte à Phase 1.

## Racionalizações comuns

| Desculpa | Realidade |
|--------|---------|
| "Issue is simple, don't need process" | Issues simples também têm causa raiz. O processo é rápido em bugs simples. |
| "Emergency, no time for process" | Depuração sistemática é MAIS RÁPIDA do que ficar batendo cabeça. |
| "Just try this first, then investigate" | O primeiro fix define o padrão. Faça certo desde o início. |
| "I'll write test after confirming fix works" | Fixes não testados não duram. Teste primeiro prova que funciona. |
| "Multiple fixes at once saves time" | Não dá para isolar o que funcionou. Causa novos bugs. |
| "Reference too long, I'll adapt the pattern" | Entendimento parcial garante bugs. Leia por completo. |
| "I see the problem, let me fix it" | Ver sintomas ≠ entender causa raiz. |
| "One more fix attempt" (após 2+ falhas) | 3+ falhas = problema arquitetural. Questione o padrão, não corrija de novo. |
| "I'll just grep for it" | grep é text matching. Use tools de LSP para análise semântica de código. |

## Referência rápida

| Phase | Atividades-chave | Critério de sucesso |
|-------|---------------|------------------|
| **1. Causa raiz** | get_diagnostics, search_symbols, find_references, reproduzir, reunir evidência | Diagnostic Evidence produzida |
| **2. Padrão** | Encontrar exemplos funcionais, comparar | Identificar diferenças |
| **3. Hipótese** | Formular teoria, testar mínimo | Confirmada ou nova hipótese |
| **4. Implementação** | get_diagnostics pré/pós, criar teste, corrigir, verificar | Bug resolvido, zero novos diagnostics |

## Quando o processo revela "sem causa raiz"

Se a investigação sistemática revelar que o problema é realmente ambiental, dependente de timing ou externo:

1. Você concluiu o processo
2. Documente o que investigou
3. Implemente o tratamento adequado (retry, timeout, mensagem de erro)
4. Adicione monitoramento/log para investigação futura

**Mas:** 95% dos casos de "sem causa raiz" são investigação incompleta.

## Técnicas de apoio

Estas técnicas fazem parte da depuração sistemática e estão disponíveis neste diretório:

- **`root-cause-tracing.md`**, rastreie bugs para trás pelo call stack até encontrar o trigger original
- **`defense-in-depth.md`**, adicione validação em múltiplas camadas após encontrar a causa raiz
- **`condition-based-waiting.md`**, substitua timeouts arbitrários por polling de condição

**Skills relacionadas:**
- **superpowers:test-driven-development**, para criar o caso de teste falhando (Phase 4, Step 2)
- **superpowers:verification-before-completion**, para verificar se o fix funcionou antes de declarar sucesso
