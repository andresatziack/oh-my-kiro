# Design da Arquitetura de Hooks

> Referência canônica do sistema de hooks. Todas as mudanças de hook devem estar em conformidade com este documento.
> **Status:** Active | **Data:** 2026-02-18

## Princípios de Design

### Sistema de Três Categorias

| Categoria | Diretório | Comportamento de saída | Propósito | Bypass |
|-----------|-----------|------------------------|-----------|--------|
| **security** | `hooks/security/` | exit 2 = bloqueio rígido | Invariantes de segurança incondicionais (comandos perigosos, secrets, fronteira do workspace) | Nenhum - nunca pode ser ignorado |
| **gate** | `hooks/gate/` | exit 2 = bloqueio rígido | Imposição de workflow (plan obrigatório, ralph loop, testes de regressão) | Arquivos marcadores `.skip-plan`, `.skip-ralph` |
| **feedback** | `hooks/feedback/` | exit 0 = consultivo | Injeção de contexto, auto-test, rastreamento de progresso, verificação de conclusão | Sempre executa, agente pode ignorar a saída |

**Regra de decisão:** Se a restrição nunca pode ser violada -> security. Se ela impõe um passo de workflow com cenários legítimos de bypass -> gate. Se ela fornece informação ou produz efeitos colaterais -> feedback.

### Esclarecimentos de Fronteira

- `gate/pre-write.sh` contém uma função consultiva (`inject_plan_context`) ao lado de gates bloqueantes. Isso é intencional - a parte consultiva pega carona no mesmo parse de stdin para evitar uma invocação separada de hook. A categoria do arquivo é gate (seu propósito primário é bloquear).
- `feedback/post-write.sh` retorna exit 1 em falha de teste. PostToolUse exit 1 é tratado como consultivo pela plataforma - não bloqueia o write. A categoria do arquivo é feedback.
- Shadow hooks (scripts chamados internamente por outros hooks, não registrados em config) são categorizados pela categoria de quem os chama.

### Invariantes Centrais

1. **Fonte única de config:** `scripts/generate_configs.py` gera todos os arquivos de config. Nunca edite à mão `.claude/settings.json` ou `.kiro/agents/*.json`.
2. **enforcement.md é a SoT da camada de design:** `.kiro/rules/enforcement.md` define quais hooks existem, sua classificação e seu propósito. `generate_configs.py` é a SoT da camada de config (qual hook se registra em qual agente/evento). Quando eles divergem, conserte o gerador para corresponder ao enforcement.md.
3. **As-code prevalece sobre as-text:** Se uma restrição pode ser imposta por um hook, não dependa do AGENTS.md ou de rules/ para impô-la.

## Registro de Hooks

### Hooks Diretos (registrados em config)

| # | Hook | Path | Evento(s) | Categoria | Dependências |
|---|------|------|-----------|-----------|--------------|
| 1 | Bloqueador de comando perigoso | `hooks/security/block-dangerous.sh` | PreToolUse[bash] | security | common.sh, patterns.sh, block-recovery.sh |
| 2 | Bloqueador de vazamento de secret | `hooks/security/block-secrets.sh` | PreToolUse[bash] | security | common.sh, patterns.sh, block-recovery.sh |
| 3 | Bloqueador de sed/awk em JSON | `hooks/security/block-sed-json.sh` | PreToolUse[bash] | security | common.sh, block-recovery.sh |
| 4 | Guarda de fronteira do workspace | `hooks/security/block-outside-workspace.sh` | PreToolUse[bash,write] | security | common.sh, block-recovery.sh |
| 5 | **Dispatcher de saída pre-bash** | `hooks/dispatch-pre-bash.sh` | PreToolUse[bash] | dispatcher | security/\*, gate/enforce-ralph-loop.sh, gate/require-regression.sh |
| 6 | **Dispatcher de saída pre-write** | `hooks/dispatch-pre-write.sh` | PreToolUse[write] | dispatcher | security/block-outside-workspace.sh, gate/pre-write.sh, gate/enforce-ralph-loop.sh |
| 7 | Pre-write gate mesclado | `hooks/gate/pre-write.sh` | PreToolUse[write] (via dispatcher) | gate | common.sh, patterns.sh |
| 8 | Enforcer de ralph loop | `hooks/gate/enforce-ralph-loop.sh` | PreToolUse[bash,write] (via dispatcher) | gate | common.sh |
| 9 | Gate de teste de regressão | `hooks/gate/require-regression.sh` | PreToolUse[bash] (via dispatcher, somente pilot) | gate | common.sh |
| 10 | Post-write feedback mesclado | `hooks/feedback/post-write.sh` | PostToolUse[write] | feedback | common.sh |
| 11 | Logger de execução bash | `hooks/feedback/post-bash.sh` | PostToolUse[bash] | feedback | common.sh |
| 12 | Detector de correção | `hooks/feedback/correction-detect.sh` | UserPromptSubmit | feedback | - |
| 13 | Inicializador de sessão | `hooks/feedback/session-init.sh` | UserPromptSubmit | feedback | - |
| 14 | Enriquecimento de contexto | `hooks/feedback/context-enrichment.sh` | UserPromptSubmit | feedback | - |
| 15 | Verificador de conclusão | `hooks/feedback/verify-completion.sh` | Stop | feedback | common.sh |

### Shadow Hooks (chamados internamente, não em config)

| # | Hook | Path | Chamado por | Propósito |
|---|------|------|-------------|-----------|
| 14 | Auto-capture | `hooks/feedback/auto-capture.sh` | correction-detect.sh | Grava correção em episodes.md |
| 15 | KB health report | `hooks/feedback/kb-health-report.sh` | verify-completion.sh | Gera relatório de saúde da knowledge base |

### Bibliotecas Compartilhadas (`_lib/`)

| Arquivo | API | Usado por | Contrato |
|---------|-----|-----------|----------|
| `common.sh` | `hook_block()`, `file_mtime()`, `detect_test_command()`, `is_source_file()`, `is_test_file()`, `find_active_plan()` | Todos os hooks | Estável - mudanças não podem quebrar callers existentes. Novas funções: adicionar, não modificar assinaturas. |
| `patterns.sh` | `DANGEROUS_BASH_PATTERNS[]`, `INJECTION_PATTERNS`, `SECRET_PATTERNS` | hooks de security, pre-write.sh | Arrays append-only. Nunca remova padrões sem revisão de segurança. |
| `block-recovery.sh` | `hook_block_with_recovery()` | hooks de security | Encapsula `hook_block()` com contagem de retry e lógica de skip-after-3. |

### Matriz de Registro de Agentes

Agentes Kiro registram scripts dispatcher (linhas 1-2 abaixo). O settings.json do CC registra hooks individuais (sem camada dispatcher).

| Hook | default | pilot | executor | researcher | reviewer | CC settings.json |
|------|---------|-------|----------|------------|----------|-------------------|
| dispatch-pre-bash | ✅ | ✅(+regression) | ✅(SKIP_GATE=1) | ✅(SKIP_GATE=1) | ✅(SKIP_GATE=1) | - |
| dispatch-pre-write | ✅ | ✅ | - | - | - | - |
| block-dangerous | via dispatch | via dispatch | via dispatch | via dispatch | via dispatch | ✅ |
| block-secrets | via dispatch | via dispatch | via dispatch | via dispatch | via dispatch | ✅ |
| block-sed-json | via dispatch | via dispatch | via dispatch | via dispatch | via dispatch | ✅ |
| block-outside-workspace | via dispatch | via dispatch | via dispatch | via dispatch | via dispatch | ✅ |
| pre-write | via dispatch | via dispatch | - | - | - | ✅ |
| enforce-ralph-loop | via dispatch | via dispatch | - | - | - | ✅ |
| require-regression | - | via dispatch | - | - | - | - |
| post-write | ✅ | ✅ | - | - | - | ✅ |
| post-bash | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| correction-detect | ✅ | ✅ | - | - | - | ✅ |
| session-init | ✅ | ✅ | - | - | - | ✅ |
| context-enrichment | ✅ | ✅ | - | - | - | ✅ |
| verify-completion | ✅ | ✅ | - | - | - | ✅ |

## Ciclo de Vida

### Adicionando um Novo Hook

1. **Classifique** - Use a árvore de decisão na seção Extensibilidade abaixo.
2. **Escreva o script** - Coloque em `hooks/<categoria>/`, importe `_lib/common.sh`. Nomeação: `verb-noun.sh`.
3. **Atualize enforcement.md** - Adicione linha ao Registro de Hooks em `.kiro/rules/enforcement.md`.
4. **Atualize o gerador** - Adicione o hook em `scripts/generate_configs.py` no(s) builder(s) de agente apropriado(s).
5. **Regenere os configs** - `python3 scripts/generate_configs.py`
6. **Valide** - `python3 scripts/generate_configs.py --validate`
7. **Escreva testes** - Adicione em `tests/hooks/`.
8. **Atualize este doc** - Adicione linha ao Registro de Hooks e à Matriz de Registro de Agentes acima.

### Modificando um Hook Existente

1. Faça as mudanças no script.
2. Rode os testes existentes: `bash tests/hooks/test-kiro-compat.sh`
3. Se mudar assinaturas de função em `_lib/`: cheque todos os callers primeiro.
4. Atualize enforcement.md se evento, tipo ou propósito do hook mudou.
5. Rode `python3 scripts/generate_configs.py --validate`
6. Atualize este doc se a informação de registro mudou.

### Depreciando um Hook

1. Marque `deprecated` no registro de enforcement.md com motivo e substituto.
2. Remova de `scripts/generate_configs.py`.
3. Regenere configs: `python3 scripts/generate_configs.py`
4. Mova o script para `.trash/` (preserve para recuperação).
5. Atualize este doc - mova do registro para uma seção "Depreciado".
6. Limpe `.trash/` na próxima major version.

### Regras de Shadow Hook

- Um shadow hook é um script chamado por outro hook via `bash "$(dirname "$0")/script.sh"`, não registrado em nenhum config.
- Shadow hooks devem estar listados na tabela Shadow Hooks acima.
- Quem chama é responsável pelo tratamento de erro - falhas de shadow hook não podem derrubar quem chama.
- Para promover um shadow hook a hook direto: siga o fluxo "Adicionando" acima.

## Extensibilidade

### Árvore de Decisão de Classificação

```
New constraint needed
  ├── Can it be violated without safety risk?
  │   ├── No → security/ (exit 2, no bypass)
  │   └── Yes ↓
  ├── Does it enforce a workflow step?
  │   ├── Yes → gate/ (exit 2, bypass via marker file)
  │   └── No ↓
  └── It provides information or side-effects
      └── feedback/ (exit 0, advisory)
```

### Cobertura de Eventos e Pontos de Extensão

| Evento | Hooks atuais | Como estender |
|--------|--------------|---------------|
| PreToolUse[bash] | 4 security + 2 gate | Adicione padrões em `patterns.sh` antes de criar novos hooks |
| PreToolUse[write] | 1 gate (pre-write.sh, multi-fase) | Adicione novas fases em pre-write.sh |
| PostToolUse[write] | 1 feedback (post-write.sh, multi-função) | Adicione funções em post-write.sh |
| PostToolUse[bash] | 1 feedback | Estenda post-bash.sh |
| UserPromptSubmit | 3 feedback | Adicione padrões de detecção em hooks existentes primeiro |
| Stop | 1 feedback | Estenda verify-completion.sh |

**Eventos futuros:** Quando o Kiro CLI adicionar novos eventos (por exemplo, `agentSpawn`, `SessionEnd`), crie novos scripts de hook seguindo o fluxo "Adicionando". Não readapte hooks existentes.

### Extensão de Biblioteca Compartilhada

- **`common.sh`:** Funções append-only. Documente com comentário de uma linha. Não mude assinaturas existentes.
- **`patterns.sh`:** Arrays append-only. Nunca remova padrões sem revisão de segurança.
- **Novos arquivos `_lib/`:** Permitidos para capacidades genuinamente novas. Devem ser importados explicitamente - sem auto-loading.

### Padrão Dispatcher

PreToolUse pode acumular stderr de múltiplos hooks em uma única resposta (Kiro concatena todas as saídas dos hooks). Para evitar poluição de contexto por múltiplas mensagens de bloqueio, um único script dispatcher é registrado por matcher. O dispatcher chama sub-hooks como processos filho, captura seu stderr, aplica um budget global de saída (`printf '%.200s'`) e falha rápido no primeiro bloqueio.

**dispatch-pre-bash.sh** (PreToolUse[execute_bash]):
- Chama: security/block-dangerous.sh -> security/block-secrets.sh -> security/block-sed-json.sh -> security/block-outside-workspace.sh -> gate/enforce-ralph-loop.sh (-> gate/require-regression.sh se INCLUDE_REGRESSION=1)
- Env: `SKIP_GATE=1` pula hooks de gate (modo só-segurança para subagentes); `INCLUDE_REGRESSION=1` adiciona require-regression.sh (agente pilot)

**dispatch-pre-write.sh** (PreToolUse[fs_write]):
- Chama: security/block-outside-workspace.sh -> gate/pre-write.sh -> gate/enforce-ralph-loop.sh
- Nota: `gate/pre-write.sh` já é um hook mesclado (funções internas). Esse dispatcher o envolve como camada externa de output budget.

**Output budget:** `printf '%.200s' "$stderr"` (compatível com bash 3.2 - `${var:0:200}` é só bash 4+).

### Estratégia de Hook Mesclado

`pre-write.sh` e `post-write.sh` mesclam múltiplos hooks lógicos em um único script para reduzir overhead de invocação:

1. Prefira adicionar uma fase/função ao hook mesclado existente em vez de criar um novo script.
2. Cada fase precisa ser uma função nomeada com cabeçalho de comentário claro.
3. Numeração de fase precisa ser sequencial (0, 1, 2, ...) correspondendo à ordem de execução.
4. Fases de gate (exit 2) precisam vir antes das fases consultivas (exit 0).
