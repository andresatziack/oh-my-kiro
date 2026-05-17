# oh-my-kiro

[![Release](https://img.shields.io/github/v/release/KaimingWan/oh-my-kiro)](https://github.com/KaimingWan/oh-my-kiro/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tests: 56](https://img.shields.io/badge/tests-56_passing-green)]()

**Seu agente de IA esquece tudo. O meu não.**

oh-my-kiro é um framework que dá ao seu agente de IA de coding memória persistente, workflows determinísticos e inteligência que evolui sozinha. Como o oh-my-zsh para o Zsh, mas para agentes de IA.

_Dia 1: agente genérico. Dia 30: conhece sua base de código, seu estilo, seus padrões de decisão._

Funciona com: **Kiro CLI**

[Quick Start](#quick-start) • [Por que OMK](#why-oh-my-kiro) • [Comandos](#commands) • [Arquitetura](#architecture)

---

## Quick Start

**Projeto novo:**
```bash
git clone https://github.com/KaimingWan/oh-my-kiro.git my-project
cd my-project
python3 scripts/generate_configs.py
```

**Projeto existente:**
```bash
git submodule add https://github.com/KaimingWan/oh-my-kiro.git oh-my-kiro
bash oh-my-kiro/tools/init-project.sh . "My Project"
```

**Comece a construir:**
```
@auto build a REST API for user management
```

É só isso. O agente entende os requisitos, escreve um plan, faz review e executa, tudo de forma autônoma.

---

## Why oh-my-kiro?

### O problema central: agentes de IA alucinam e perdem o rumo

Você diz ao agente "sempre rode os testes antes de commitar". Ele faz isso, durante 3 turnos. Depois esquece. Ou "roda" os testes imprimindo "tests passed" sem nunca executá-los de verdade. Ou pula a etapa porque "a mudança é trivial".

**Instruções em linguagem natural são pouco confiáveis.** O agente as interpreta de forma probabilística. Pode seguir. Pode não seguir. Não dá para construir um workflow confiável em cima de "talvez".

### A solução: enforcement como código, baseado em hooks

A filosofia de design do OMK: **se algo pode ser garantido por código, não tente garantir com palavras.**

- ❌ Prompt: "Nunca commite secrets" → o agente pode commitar mesmo assim
- ✅ Hook: `block-secrets.sh` escaneia todo `git push` → exit 2 = bloqueado. Sem exceções.

- ❌ Prompt: "Sempre rode testes depois de editar" → o agente pula quando o contexto está apertado
- ✅ Hook: `post-write.sh` dispara lint + test automaticamente a cada save de arquivo. O agente não escolhe.

- ❌ Prompt: "Siga o plan passo a passo" → o agente pula etapas ou se adianta
- ✅ Hook: `enforce-ralph-loop.sh` bloqueia edições diretas no código quando existe um plan ativo. Tem que passar pelo Ralph Loop.

Não é sobre restringir o agente. É sobre **aumentar a taxa de sucesso de cada operação** removendo a possibilidade de atalhos alucinados.

### O que você ganha

- **O agente nunca esquece** - As correções persistem entre sessões. Erros viram regras. O conhecimento acumula juros.
- **19 hooks impõem, não sugerem** - O agente literalmente não consegue dar `rm -rf /`, commitar secrets, pular testes ou editar arquivos fora do seu workspace.
- **Crash do agente não importa** - O Ralph Loop continua spawnando agentes novos até cada item da checklist passar.
- **Plan → Review → Ship em um único comando** - `@auto` vai de uma ideia vaga até código merged.
- **Segurança na supply chain de skills** - Scan de ameaças em 8 categorias em todo skill instalado. Baseado na pesquisa [ToxicSkills da Snyk](https://snyk.io/blog/toxicskills-malicious-ai-agent-skills-clawhub/).
- **Zero config, poder total** - Funciona out of the box.

---

## A inovação: determinismo em 3 camadas

```
┌─────────────────────────────────────────────────────┐
│  L1: Commands — 15 workflows, 100% deterministic     │
│  @plan @auto @execute @review @evaluate @debug ...   │
│  Each hardcodes the full step chain. No shortcuts.   │
├─────────────────────────────────────────────────────┤
│  L2: Gates — 11 hooks, hard block (exit 2 = denied)  │
│  Agent CANNOT bypass. Secrets blocked. rm -rf blocked.│
│  Writes outside workspace blocked. No exceptions.    │
├─────────────────────────────────────────────────────┤
│  L3: Feedback — 8 hooks, advisory enrichment         │
│  Auto-lint on save. Correction detection. Semantic   │
│  knowledge injection on every prompt.                │
└─────────────────────────────────────────────────────┘
```

**Por que 3 camadas, em vez de só "adicionar mais hooks"?**

Nem tudo deve ser um hard block. Bloquear `rm -rf` é óbvio (L2). Mas "você deveria rodar os testes" funciona melhor como feedback automático (L3): o agente vê o resultado dos testes e se autocorrige. E "siga este workflow de 5 passos" fica melhor como comando determinístico (L1): o agente não interpreta, ele executa.

As camadas mapeiam para **níveis de certeza**: L1 = 100% (workflow disparado pelo usuário), L2 = 100% (hard block), L3 = ~50% (advisory; o agente pode ignorar, mas em geral não ignora porque o feedback é útil).

**L1 é determinístico.** Quando você diz `@plan`, o agente segue: deep understanding → escrever plan com checklist TDD → despachar reviewers paralelos → corrigir até APPROVE → executar via Ralph Loop. Não dá para pular etapas.

**L2 é uma parede dura.** `exit 2` em qualquer gate hook = operação bloqueada. O agente vê o block, recebe uma alternativa sugerida e tenta de novo de forma segura. Nenhum prompt engineering burla isso.

**L3 são juros compostos.** Cada correção que você faz é detectada, persistida em `episodes.md` e injetada automaticamente em sessões futuras por keyword match. Após 3 correções parecidas, ela é promovida a regra permanente.

---

## A inovação: Ralph Loop

Seu agente trava no meio da tarefa? A janela de contexto enche? Sem problema.

```
Ralph Loop (Python outer loop)
  │
  ├─ Spawn fresh Kiro CLI instance
  │    └─ Agent reads plan, works on next unchecked item
  │    └─ Marks item [x] when verify command passes
  │    └─ Agent exits (crash, context full, or done)
  │
  ├─ Re-verify: run all inline verify commands
  │    └─ Revert any [x] items whose verify fails
  │
  ├─ Progress check
  │    └─ Items completed? → spawn next iteration
  │    └─ 3 stalls? → circuit breaker, stop
  │
  └─ All items [x]? → ✅ Done. Print summary.
```

Cada iteração começa com **contexto limpo**. Sem acúmulo de estado velho. O loop em bash é a camada de confiabilidade; a inteligência do agente é a camada de execução.

---

## Commands

Comandos vêm em dois sabores:
- **MCP Prompt** (`@o/plan "build a REST API"`) aceita entrada em linguagem natural inline. O agente recebe sua descrição como contexto.
- **Command-only** (`@execute`, `@cpu`) disparado por keyword, sem argumentos inline. Lê estado dos arquivos (plan ativo, git diff, etc.).

### 🚀 O espectro de autonomia

#### `@auto` "build a user auth system" _(MCP prompt)_
**Piloto automático completo.** Um comando → entender requisitos → escrever plan com checklist TDD → despachar reviewers paralelos → auto-fix até APPROVE → execução via Ralph Loop → done.

_O que o torna especial:_ Readiness Check, uma checklist de 4 dimensões (Goal / Constraints / Success Criteria / Context) que valida o entendimento antes de qualquer linha de código. Se algo está obscuro, ele faz exatamente UMA pergunta com modos de challenge socrático.

#### `@plan` "migrate from PostgreSQL to DynamoDB" _(MCP prompt)_
**Execução controlada.** Mesmo pipeline do `@auto`, mas pausa para sua confirmação após a Phase 0 (deep understanding) e após o review. Você fica no loop.

_O que o torna especial:_ todo item da checklist exige um comando de verify inline (`- [ ] API returns 200 | \`curl -sf localhost:8000/health\``). O Ralph Loop re-executa esses comandos e reverte qualquer `[x]` que falhar. Sem completion falsa.

#### `@execute` _(command-only)_
**Retomar e finalizar.** Carrega um plan aprovado, dispara o Ralph Loop. Crashes do agente não importam: o loop em bash continua spawnando instâncias novas até cada item da checklist passar.

_O que o torna especial:_ isolamento de Work Dir. Se o plan declara `**Work Dir:** worktrees/omk-foo`, a execução fica sandboxed ali. O gate hook bloqueia writes fora desse diretório.

#### `@do` "add a health check endpoint" _(MCP prompt)_
**Tarefa rápida (< 1 hora).** Sem arquivo de plan, sem despacho de review. Scratchpad → implementar → verify → commit. Para quando `@plan` é exagero.

---

### 🔍 Comandos de análise

#### `@review` _(MCP prompt)_
Despacha um subagente reviewer com o git diff completo. Review multi-ângulo (correctness, segurança, performance). Cada finding tem severidade P0-P3 e citação file:line. Detecta automaticamente o contexto de worktree pelo `.active-submodule`.

#### `@evaluate` "scripts/ralph_loop.py look for simplifications" _(MCP prompt)_
**Avaliação independente de qualidade de código.** 4 subagentes evaluators paralelos, cada um com uma persona distinta (Refactoring Expert, Product Manager, Breaker, CSO), avaliam o código em 6 dimensões: Simplicidade, Alinhamento, Correctness, Segurança, Robustez, Manutenibilidade. O formato obrigatório de fill-table impede reviews superficiais. Também roda automaticamente após o `@execute` terminar (loop adversarial inspirado em GAN, até 3 rodadas).

#### `@debug` "tests fail with timeout on CI" _(MCP prompt)_
**Pipeline sistemático de debugging.** Não é tentativa-e-erro: é análise estruturada de causa raiz:

1. Resumo de sessão: checa `docs/investigations/` por trabalho anterior nesse bug (continuidade entre sessões)
2. Triagem: lê `episodes.md` em busca de padrões conhecidos, monta contexto arquitetural via LSP
3. Árvore de hipóteses: gera hipóteses ranqueadas, testa cada uma com evidência
4. Fix: somente após a causa raiz ser confirmada

_O que o torna especial:_ os documentos de investigação persistem entre sessões. Se você esbarra num bug na segunda e retoma na quarta, o agente continua exatamente de onde parou.

#### `@research` "how does Kafka handle rebalancing" _(MCP prompt)_
**Research em 3 níveis:** L0 conhecimento built-in → L1 web search → L2 deep dive com cross-verification de fontes. Findings persistidos automaticamente em arquivo.

---

### 🔧 Comandos de Git e PR

#### `@fixpr` _(command-only)_
**PR fixer automatizado.** Busca TODAS as threads de review não resolvidas via GraphQL, faz triagem de cada comentário (fix / pushback / clarify), implementa as correções, responde e resolve cada thread. Meta: zero threads não resolvidas.

_O que o torna especial:_ PR Blueprint. Lê o diff completo primeiro para entender a intenção, depois corrige cada comentário sem se desviar do propósito do PR. A lista de Protected Code impede que reviewers solicitem mudanças em decisões de design intencionais.

#### `@cpr` _(MCP prompt)_ · `@cpu` _(command-only)_
`@cpr`: commit → push → criar PR → cleanup do worktree. `@cpu`: commit → push → merge direto.

#### `@ck` "feature/auth" _(MCP prompt)_ · `@wt` _(command-only)_
`@ck`: checkout de uma branch num worktree do submodule com fuzzy search. `@wt`: lista todos os worktrees, faz cleanup das branches já merged.

---

### 🧠 Comandos de conhecimento

#### `@dream` _(command-only)_
**Higiene automatizada do conhecimento.** Escaneia toda a base de conhecimento atrás de podridão:
- Determinístico (bash): links mortos, episodes obsoletos, arquivos órfãos, marcadores TODO, staleness por tipo
- Semântico (LLM): redundância de conteúdo, contradições entre arquivos, recomendações de consolidação

#### `@agent` _(MCP prompt)_ · `@know` _(MCP prompt)_
`@agent`: destila um princípio em `rules.md`. `@know`: captura um insight de conhecimento em `episodes.md`.

#### `@lint` _(command-only)_ · `@skill` _(command-only)_
`@lint`: health check do framework. `@skill`: lista as skills, casa a necessidade do usuário com a mais próxima.

---

## A inovação: sistema de conhecimento auto-evolutivo

Isso não é "salvar notas num arquivo". É um **pipeline de inteligência em loop fechado** que detecta erros automaticamente, extrai padrões e religa o comportamento do agente, de forma permanente.

### How It Works

```
You say "别用 sed 改 JSON，用 jq"
  │
  ├─ correction-detect.sh fires (中英文 30+ 纠正模式匹配)
  │
  ├─ auto-capture.sh pipeline:
  │    ├─ Gate 1: 过滤低价值 (问句丢弃, 无动作丢弃)
  │    ├─ Gate 2: 提取关键词 (英文技术术语优先, 中文动作词 fallback)
  │    ├─ Gate 3: 去重 (已在 rules.md → 跳过)
  │    └─ 写入 episodes.md: "2026-03-30 | active | sed,json,jq | 别用 sed 改 JSON"
  │
  ├─ distill.sh (background):
  │    └─ 同一关键词出现 ≥3 次 → 自动提升为 rules.md 永久规则
  │    └─ 标记源 episodes 为 "promoted"，下次 session-init 清理
  │
  └─ context-enrichment.sh (every prompt):
       └─ 用户消息包含 "sed" 或 "json" → 自动注入对应规则
       └─ 🔴 CRITICAL 规则: 每条消息都注入
       └─ 🟡 RELEVANT 规则: 关键词匹配时注入
```

### O que torna isso diferente

**Não é só memória, é sistema imune.** O agente não apenas "lembra" da sua correção. Ele constrói anticorpos:

1. **Detecção em tempo real** - `correction-detect.sh` casa 30+ padrões de correção em chinês e inglês ("你错了", "不是这样", "wrong approach", "try again"). Sem tagging manual.

2. **Gates de qualidade** - Nem toda correção vale persistência. `auto-capture.sh` filtra perguntas, reclamações vagas e duplicatas. Só sobrevivem correções acionáveis com keywords extraíveis.

3. **Auto-promoção** - Quando o mesmo padrão de keyword aparece em 3+ episodes, o `distill.sh` o promove automaticamente para regra permanente, com nível de severidade (🔴 CRITICAL = sempre injetado, 🟡 RELEVANT = injetado por keyword match).

4. **Injeção inteligente** - `context-enrichment.sh` roda em todo prompt do usuário. Faz keyword match da mensagem contra as seções de `rules.md` e injeta apenas as regras relevantes. Não o arquivo inteiro: só o que importa para essa mensagem específica. Budget: no máximo 3 regras por mensagem.

5. **Continuidade entre sessões** - `session-init.sh` faz cleanup dos episodes promovidos, lembra dos candidatos a promoção e bootstrapa o estado de conhecimento. Dia 1 e Dia 100 usam o mesmo pipeline.

6. **Busca semântica (opcional)** - Com OpenViking configurado, o `context-enrichment.sh` também consulta um índice semântico de todos os arquivos de conhecimento, injetando snippets relevantes mesmo quando o keyword match falha.

### Exemplo real de produção

Após 3 correções sobre compatibilidade com macOS, o sistema promoveu automaticamente esta regra:

> 🔴 macOS 没有 `timeout` 命令 (GNU coreutils). Plan 里写 `timeout 60s` 在 macOS 上会 command not found. 替代: `gtimeout` (brew install coreutils). 所有跨平台 bash 脚本不能假设 timeout 存在.

Agora, toda vez que o agente escreve um script bash, essa regra é injetada. O erro não acontece de novo.

### Higiene de conhecimento: `@dream`

Conhecimento apodrece. Correções antigas viram irrelevantes. Arquivos se contradizem. `@dream` é o faxineiro automatizado:

- **Determinístico (bash):** links mortos, episodes obsoletos (>14d → auto-resolvidos), arquivos órfãos, marcadores TODO, staleness por tipo
- **Semântico (LLM):** redundância de conteúdo entre arquivos, contradições de dados (por exemplo, "GitHub Stars 8.5K" em um arquivo vs "10K+" em outro), recomendações de consolidação com prioridade

---

## Segurança

### Enforcement no nível dos hooks

| O que é bloqueado | Como |
|---------------|-----|
| `rm -rf`, `sudo`, `curl\|bash` | `security/block-dangerous.sh`, hard block |
| API keys, chaves privadas em commits | `security/block-secrets.sh`, scan no pre-push |
| `sed`/`awk` em arquivos JSON | `security/block-sed-json.sh`, use jq |
| Writes de arquivo fora do workspace | `security/block-outside-workspace.sh` |
| Edições no source sem plan ativo | `gate/enforce-ralph-loop.sh` |
| Writes fora do Work Dir declarado | `gate/enforce-work-dir.sh` |

### Supply chain de skills

Toda instalação de skill passa pelo `audit-skill.sh`, um scan de ameaças em 8 categorias:

| Ameaça | Severidade |
|--------|----------|
| Prompt injection, ofuscação base64, jailbreaks | 🔴 CRITICAL |
| eval/exec, shell=True, backdoors | 🔴 CRITICAL |
| curl\|bash, archives protegidos por senha | 🔴 CRITICAL |
| Leitura de ~/.aws/credentials, echo de API keys | 🟠 HIGH |
| Secrets hardcoded (AWS keys, GitHub tokens) | 🟠 HIGH |
| Fetches HTTP externos, imports dinâmicos | 🟡 MEDIUM |
| sudo, modificações no systemctl | 🟡 MEDIUM |

CRITICAL = bloqueado. HIGH = aviso. Toda instalação tem gate. Não é permitido `npx skills add` direto.

---

## Integração total com a plataforma Kiro

OMK foi feito para explorar todas as capacidades da plataforma Kiro. Não só hooks: a stack inteira.

### Steering Rules (`.kiro/rules/`)

As steering rules do Kiro são instruções always-on injetadas em toda interação do agente. OMK usa 4 arquivos de steering como "constituição":

| Arquivo | O que ele direciona |
|------|---------------|
| `enforcement.md` | Registro completo de hooks com tipos de event, camadas de determinismo (L0-L3), regras de geração de config |
| `code-analysis.md` | **Mandato LSP-first.** O agente deve usar `search_symbols`, `find_references`, `get_diagnostics` antes de grep. Busca por padrão AST antes de busca textual. `pattern_rewrite` antes de sed. |
| `commands.md` | Tabela de roteamento de comandos: qual `@command` dispara qual workflow |
| `reference.md` | Convenções do projeto, padrões de nomenclatura, regras de organização de arquivos |

_Por que isso importa:_ as steering rules são injetadas pela plataforma, não pelo agente. O agente não pode escolher ignorá-las. Essa garantia é mais dura que instruções no AGENTS.md.

### Inteligência de código LSP-first

A maioria dos agentes de IA lê código com `grep` e `cat`. Os agentes do OMK usam **Language Server Protocol**, a mesma inteligência que alimenta sua IDE:

```
# Instead of: grep -rn "handleRequest" src/
# OMK agent does:
search_symbols("handleRequest")     → find definition
find_references(file, line, col)    → find all callers
get_hover(file, line, col)          → get type signature
get_diagnostics(file)               → get compiler errors
pattern_search("try { $$$ } catch") → find all error handlers (AST-level)
```

Configurado via `.kiro/settings/lsp.json` com suporte a Rust, Python, TypeScript, Go e mais. A steering rule `code-analysis.md` faz enforcement: o agente é direcionado para longe do grep em navegação de código.

### Skills, Hooks, Tools, fonte única da verdade

```
hooks/     ─── symlinked ──→  .kiro/hooks
skills/    ─── symlinked ──→  .kiro/skills
commands/  ─── symlinked ──→  .kiro/prompts
```

Você edita em `hooks/`, `skills/`, `commands/`. O diretório `.kiro/` é gerado. `scripts/generate_configs.py` produz os configs de agentes, settings e wiring a partir dessas fontes. Nunca edite `.kiro/` direto.

| Recurso do Kiro | Uso no OMK |
|-------------|-----------|
| **Hooks** (PreToolUse/PostToolUse/Stop) | 19 hooks: gates de segurança, enforcement de workflow, auto-lint, detecção de correção, injeção de conhecimento |
| **Skills** (capacidades on-demand) | 14 skills: planning, reviewing, coding, debugging, research, self-reflect, etc. |
| **Prompts** (comandos MCP) | 10 MCP prompts aceitando linguagem natural: `@o/plan "build X"`, `@o/debug "Y fails"` |
| **Agents** (configs de subagentes) | 5 perfis: pilot, reviewer, researcher, executor, default |
| **Steering** (regras always-on) | 4 arquivos de regra: enforcement, code-analysis, commands, reference |
| **Settings** (LSP + MCP) | LSP para 5+ linguagens, MCP server para registro de prompts |

---

```
oh-my-kiro/
├── commands/        # 14 custom commands (single source of truth)
├── hooks/
│   ├── security/    # 4 hard blocks
│   ├── gate/        # 7 enforcement gates
│   ├── feedback/    # 8 advisory hooks
│   └── _lib/        # Shared: patterns, distill, OV client
├── skills/          # 14 on-demand capabilities
├── scripts/
│   ├── ralph_loop.py        # The execution engine
│   ├── generate_configs.py  # Single source → platform configs
│   └── mcp-prompts.py       # MCP prompt server
├── knowledge/       # Persistent memory (rules, episodes, INDEX)
├── agents/          # Subagent prompts (reviewer, researcher)
├── tools/           # CLI: init, sync, audit, validate
└── tests/           # 56 test files
```

**Design-chave:** `hooks/`, `skills/`, `commands/` são a fonte única da verdade. Os configs da plataforma (`.kiro/`) são gerados pelo `generate_configs.py`. Nunca edite arquivos gerados.

---

## Cherry-Pick do que você precisa

| Quer | Copie |
|------|------|
| Só o motor de execução | `scripts/ralph_loop.py` + `scripts/lib/` |
| Só self-learning | `skills/omk-self-reflect/` + `knowledge/rules.md` + `knowledge/episodes.md` |
| Só os hooks de segurança | `hooks/security/` + `hooks/_lib/patterns.sh` |
| Só auditoria de skills | `tools/audit-skill.sh` + `tools/install-skill.sh` |

---

## Estendendo

Veja [EXTENSION-GUIDE.md](docs/EXTENSION-GUIDE.md) para adicionar skills, hooks e conhecimento específicos do projeto.

---

## Princípios de design

1. **Determinístico em vez de torcer** - Comandos e hard blocks, não prompts soft
2. **Acumular ao longo do tempo** - Cada sessão deixa a próxima melhor
3. **Código em vez de prosa** - Hooks impõem, palavras sugerem
4. **Evidência antes de afirmação** - Verificação primeiro, sempre
5. **Seguro por padrão** - Toda instalação de skill auditada, comandos perigosos bloqueados
6. **Reforma ousada em vez de patches tímidos** - Qualidade acima de retrocompatibilidade

---

## License

MIT
