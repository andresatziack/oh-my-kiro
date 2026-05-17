---
name: omk-skill-creation
description: "Create high-quality, production-ready skills from scratch. Trigger when user says 'create skill', 'new skill', 'write a skill', 'make a skill', '创建 skill', '写个 skill', 'skillify', or when packaging a repeated workflow into a reusable skill. Also trigger when reviewing or improving existing skills."
---

# Skill Creation, da ideia à produção

## Trigger Examples
- "把这个重复流程做成 skill"
- "create a new skill for code review"
- "帮我写一个 SEO 研究的 skill"
- "review and improve this skill"
- "这个工作流应该 skillify"

## Filosofia

> A janela de contexto é um bem público. Adicione apenas o que o agent ainda não sabe.

Uma skill é um manual de onboarding para o agent, depois de lê-la, o agent sabe seu processo, padrões e preferências sem precisar reensinar a cada sessão.

## Phase 0: Isso deveria ser uma skill?

Antes de escrever qualquer coisa, decida o mecanismo certo:

| Sinal | Mecanismo |
|--------|-----------|
| Regra precisa estar em TODA conversa | AGENTS.md / rules.md |
| Precisa rodar automaticamente em eventos | Hook (gate/ ou feedback/) |
| Ensina ao agent um workflow específico | **Skill** ← você está aqui |
| Dá ao agent uma tool/API nova | MCP server |
| Precisa de execução em contexto isolado | Subagent |

**Threshold de ROI da skill**: Esse workflow vai rodar ≥3 vezes? Se não, apenas explique na conversa.

## Phase 1: Design (antes de escrever o SKILL.md)

### Step 1: Defina casos de uso

Escreva de 3 a 5 prompts concretos do usuário que devem disparar essa skill. Não descrições abstratas, frases reais que usuários vão digitar:

```
Example for a "daily planning" skill:
- "plan my day"
- "start work"
- "今天做什么？"
- "morning routine"
- "daily standup prep"
```

Esses prompts moldam tudo: nome da skill, description, input/output, steps do workflow.

### Step 2: Defina Input → Output

| Pergunta | Resposta |
|----------|--------|
| O que o usuário fornece? | (file, URL, text, nada?) |
| O que a skill produz? | (file, report, action, decision?) |
| Em que formato? | (markdown, JSON, email, code?) |

### Step 3: Escolha o pattern

| Precisa de APIs externas / dados em tempo real? | → Pattern C: Skill + MCP |
|-------------------------------------|--------------------------|
| Precisa de computação determinística? | → Pattern B: Prompt + Scripts |
| O julgamento do agent sozinho basta? | → Pattern A: Prompt-Only |

**Em caso de dúvida, comece com Pattern A.** Adicione scripts depois, se necessário.

### Step 4: Escolha o nível de liberdade

| Fragilidade | Liberdade | Exemplo |
|-----------|---------|---------|
| Alta (DB migration, deploy) | Baixa, comandos exatos, sem variação | `Run exactly: python migrate.py --verify` |
| Média (geração de código) | Média, template com parâmetros | Pseudocódigo + opções de config |
| Baixa (code review, escrita) | Alta, diretrizes + heurísticas | "Check for X, Y, Z" |

## Phase 2: Escrever o SKILL.md

### Estrutura de arquivos

```
my-skill/
├── SKILL.md              # Required. < 500 lines
├── scripts/              # Optional. Deterministic code
├── references/           # Optional. Loaded on demand
└── assets/               # Optional. Templates, data
```

### Frontmatter (crítico)

A description determina se a skill chega a ser disparada. O agent, por padrão, NÃO dispara, sua description precisa "empurrar".

```yaml
---
name: kebab-case-name        # ≤64 chars, lowercase + hyphens only
description: >                # ≤1024 chars, third person
  [What it does]. Trigger when user says [keyword1], [keyword2],
  [keyword3], or [scenario description]. Also trigger when
  [implicit trigger condition].
---
```

**Regras:**
- Sempre em terceira pessoa ("Processes X", não "I help you" ou "You can use this")
- Primeira frase: o que faz (propósito)
- Segunda frase: keywords de trigger explícitas (liste frases reais do usuário)
- Terceira frase: triggers implícitos (tipos de arquivo, contextos, padrões)
- Seja específico > seja breve. Use os 1024 chars se precisar

**Ruim**: `description: Helps with data tasks`
**Bom**: `description: Analyze sales/revenue CSV files to find patterns and calculate metrics. Trigger when user mentions sales data, revenue analysis, profit margins, or uploads xlsx/csv with financial column headers.`

### Estrutura do corpo

```markdown
## Trigger Examples
- "realistic user prompt 1"
- "realistic user prompt 2" (different language/style)
- "realistic user prompt 3"
- "realistic user prompt 4"
- "realistic user prompt 5"

## [Workflow Steps]
Step 1: ...
Step 2: ...

## [Rules / Constraints]

## [Output Format] (if applicable)
```

### Princípios de escrita

1. **Conciso é fundamental**, o Claude é inteligente. Adicione apenas o que ele não sabe. Desafie cada parágrafo: "Justifica seu custo em tokens?"
2. **Razões > comandos**, "Show command before executing, because users need to verify safety" supera "ALWAYS show commands. NEVER execute directly."
3. **Exemplos > explicações**, um par input/output ensina mais que três parágrafos de descrição
4. **Um padrão, uma escape hatch**, não liste 5 opções. Escolha a melhor, mencione a alternativa para edge cases
5. **Terminologia consistente**, escolha um termo, use sempre. Não "endpoint/URL/route/path" indistintamente

### Disclosure progressivo

- SKILL.md = visão geral + navegação (< 500 linhas)
- `references/` = docs detalhados, carregados on demand
- `scripts/` = código executável, roda sem entrar no contexto
- Profundidade de referência: máximo 1 nível. SKILL.md → reference.md. Nunca reference.md → sub-reference.md
- Para references > 100 linhas, adicione um sumário no topo

## Phase 3: Testar

### Escreva test prompts bagunçados

Usuários reais erram digitação, usam gírias, esquecem nomes de arquivo. Teste com prompts realistas, não limpos:

```
# Good (realistic)
"ok so my boss sent me this xlsx (its in downloads, called
something like 'Q4 sales final FINAL v2.xlsx') and she wants
profit margin as a percentage"

# Bad (too clean)
"Please analyze the sales data in the uploaded Excel file
and add a profit margin column"
```

### Loop de iteração

1. Rode a skill com test prompts
2. Disparou? Se não → corrija a description
3. Produziu output correto? Se não → corrija os steps do workflow
4. Formato do output certo? Se não → corrija template/exemplos
5. Repita

### Verifique a taxa de trigger

Pedidos curtos e simples raramente disparam skills. Garanta que o set de testes inclua prompts com complexidade suficiente e keywords que casem.

## Phase 4: Checklist de review

Antes de fazer ship, verifique:

- [ ] Description é específica, inclui keywords-trigger e está em terceira pessoa
- [ ] Corpo do SKILL.md tem < 500 linhas
- [ ] Tem 5 Trigger Examples com prompts realistas
- [ ] Conteúdo longo dividido em references/
- [ ] Sem informação sensível ao tempo (ou em uma seção "old patterns")
- [ ] Terminologia consistente em todo o documento
- [ ] Exemplos concretos, não explicações abstratas
- [ ] Razões dadas para regras (não só MUST/NEVER)
- [ ] Scripts tratam erros explicitamente (não empurram para o agent)
- [ ] Sem secrets hardcoded ou magic numbers
- [ ] Testado com prompts realistas e bagunçados

## Anti-padrões

| Não faça | Faça em vez disso |
|-------|-----------|
| Empilhar tudo no SKILL.md | Divida em references/ ao chegar a 500 linhas |
| Description vaga ("helps with data") | Específica + keywords-trigger |
| Description em primeira/segunda pessoa | Sempre terceira pessoa |
| Listar 5 opções equivalentes | Um padrão + uma escape hatch |
| MUST/NEVER sem razão | Explique por que a regra existe |
| Testar só com prompts limpos | Teste com prompts realistas e bagunçados |
| Escrever a skill antes de iterar na conversa | Acerte o workflow primeiro, depois extraia |
| Referências profundamente aninhadas (A→B→C) | Máximo 1 nível |
| Assumir pacotes instalados | Liste dependências explicitamente |
| Magic numbers em scripts | Documente o motivo de cada valor |

## Convenções específicas do OMK

Ao criar skills para projetos oh-my-kiro:

1. **Nomenclatura**: prefixo `omk-` para skills do framework, nomes específicos do projeto para skills do projeto
2. **Localização**: skills do framework → `oh-my-kiro/skills/`, skills do projeto → `skills/`
3. **Segurança**: rode `bash tools/audit-skill.sh <dir>` antes de instalar skills externas
4. **Sync**: depois de criar no submodule, rode `bash tools/sync-omk.sh .` para propagar
5. **Registro**: `python3 scripts/generate_configs.py` para atualizar configs de plataforma
