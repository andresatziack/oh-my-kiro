# Descobertas - TDD Checklist Enforcement

## Pipe vs Process Substitution em Hooks Bash

**Problema:** `echo "$CONTENT" | grep ... | while read` executa o loop while em uma subshell. `exit 2` dentro do loop só encerra a subshell, não o script pai. O hook aparenta sucesso (exit 0) mesmo quando deveria bloquear.

**Solução:** Use process substitution: `while read ...; do ... done < <(echo "$CONTENT" | grep ...)`. Isso executa o loop na shell atual, e `exit 2` propaga corretamente.

**Regra:** Todos os hooks que iteram sobre conteúdo filtrado e podem precisar de `exit 2` devem usar process substitution, nunca loops while baseados em pipe.

## Teste de Lock Vivo em Hooks

**Problema:** Usar processos em background (`bash -c 'echo $$ > lock; sleep 5' &`) em suítes de teste causa hangs quando o test runner sai antes do processo em background.

**Solução:** Use o PID da shell atual (`$$`) como o PID do lock vivo - é garantido estar vivo durante a execução do teste. Sem necessidade de processos em background.

## Design de Hook Consolidado (enforce-ralph-loop)

**Decisão:** Um único hook trata tanto `execute_bash` quanto `fs_write` via variável MODE, registrado duas vezes em default.json com matchers diferentes. Isso é mais limpo do que embutir verificações de ralph-loop em pre-write.sh (separação de responsabilidades).

**Padrões-chave:**
- `case "$TOOL_NAME" in ... MODE="bash" / MODE="write"` para dispatch da tool
- Allowlist baseado em path via `case "$FILE" in` para fs_write (mais simples que regex)
- Allowlist read-only estrito + rejeição de chain para execute_bash (sem `&&`, `||`, `;`, `|`, `>`, backticks, `$(`)

## Isolamento de Hash de Workspace para Testes de Hook

**Problema:** Testes de integração que invocam hooks de segurança diretamente compartilham o mesmo arquivo `/tmp/block-count-<hash>.jsonl` com os hooks ao vivo, porque ambos rodam no mesmo diretório de workspace. Os contadores acumulam entre a sessão interativa e as execuções de teste, causando assertions instáveis.

**Solução:** Execute as invocações de hook a partir de um diretório `mktemp -d`. O `pwd | shasum` em `block-recovery.sh` produz um hash único, isolando contagens de teste das contagens de sessão ao vivo. Limpeza via `trap 'rm -rf "$TEST_DIR"' EXIT`.

## Auto-Reversão de Git Stash em ralph-loop.sh

**Problema:** `ralph-loop.sh` executa `git stash push` antes de cada iteração para salvar estado sujo. Ao testar o script com mudanças não commitadas no próprio script, o stash reverte essas mudanças no meio da execução. O script então roda a versão antiga (pré-edição).

**Solução:** Sempre commite mudanças em `ralph-loop.sh` antes de rodar testes de integração que invocam o script. O `git stash push` dentro do script é por design (protege contra estado sujo durante runs do agent), então a correção está no fluxo de trabalho, não no código.

**Regra:** Ao modificar ralph-loop.sh, commite antes de testar.

## enforce-ralph-loop Bloqueia Comandos Verify do Checklist

**Problema:** Vários comandos verify do checklist são eles próprios bloqueados por enforce-ralph-loop.sh:
- `python3 -m pytest tests/ -q` - não está no allowlist read-only
- `grep -c '|' docs/INDEX.md` - o hook interpreta `|` no padrão grep como caractere de pipe
- `diff CLAUDE.md AGENTS.md` - `diff` standalone não está no allowlist (apenas `git diff` está)

**Impacto:** Ao executar os itens finais do checklist fora do ralph-loop, os comandos verify não podem ser executados via bash. É preciso usar tools alternativas (grep tool, comando md5, fs_read) ou rodar dentro do ralph-loop.

**Recomendação:** Considere adicionar `python3 -m pytest`, `diff` e `bash -c 'test ...'` ao allowlist read-only, ou tornar a detecção de pipe mais inteligente (distinguir `|` em padrões grep de pipes shell reais).

## Bug de Path Absoluto em pre-write.sh (Compatibilidade Kiro)

**Problema:** Kiro CLI envia paths absolutos em `tool_input.path` (ex.: `/Users/.../CLAUDE.md`), mas `gate_instruction_files` em pre-write.sh só fazia match em paths relativos (`CLAUDE.md`, `./CLAUDE.md`). Isso significava que a proteção de escrita em arquivos de instrução era silenciosamente ignorada ao rodar sob Kiro.

**Correção:** Adicionada normalização de path relativo ao workspace logo após a extração de FILE:
```bash
WORKSPACE=$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")
case "$FILE" in "$WORKSPACE"/*) FILE="${FILE#$WORKSPACE/}" ;; esac
```

**Impacto:** O mesmo padrão já existia em `enforce-ralph-loop.sh`. Qualquer hook que faça matching baseado em path em `tool_input.path`/`tool_input.file_path` deve normalizar para paths relativos primeiro.

**Regra:** Todos os hooks que parseiam paths de arquivo de tool_input devem normalizar absoluto->relativo antes do matching de padrão.

## Long-Running Agent Research (2026-02-19)

> Sources: Anthropic "Effective Harnesses for Long-Running Agents" (2025-11-26), Anthropic "Effective Context Engineering for AI Agents" (2025-09-29), Manus context engineering practices, Claude Code Agent Teams/Swarm Mode (2026-02)

### Descobertas centrais

**1. Arquitetura de Agent em duas etapas no paper da Anthropic**

Inovacao central do paper: Initializer Agent (primeira session monta o ambiente) + Coding Agent (sessions seguintes avancam de forma incremental).

- Responsabilidade do Initializer Agent: escrever a feature list (formato JSON), escrever init.sh, escrever progress.txt, fazer o commit inicial no git
- Responsabilidade do Coding Agent: a cada session, ler primeiro o progress + git log + rodar os testes basicos; em seguida, executar apenas uma feature e, ao terminar, commitar e atualizar o progress
- Descoberta-chave: feature list em JSON e menos suscetivel a adulteracao pelo agent do que em Markdown
- Descoberta-chave: comecar uma feature nova sem antes validar o ambiente agrava bugs preexistentes

**2. Context Rot e Compaction**

Tese central do paper de context engineering da Anthropic: contexto e recurso finito; conforme os tokens aumentam, o orcamento de atencao se dilui (n^2 pairwise relationships).

- Pratica do Manus: cada tool result tem duas representacoes (full/compact); resultados antigos sao automaticamente substituidos pela versao compact (mantendo apenas a referencia de path)
- Plataforma Anthropic: o recurso de context editing remove automaticamente tool call results obsoletos
- Pesquisa: remover tool results antigos diretamente (sem LLM summarization) tem efeito equivalente ou superior em cenarios observation-heavy
- Principio-chave: "find the smallest possible set of high-signal tokens that maximize the likelihood of desired outcome"

**3. Evolucao da arquitetura de Sub-agent -> Agent Teams**

No inicio de 2026, o Claude Code lancou Agent Teams (Swarm Mode):

- 7 primitivas: TeamCreate, TaskCreate, TaskUpdate, TaskList, Task(team_name), SendMessage, TeamDelete
- Diferenca-chave: subagent so reporta de volta ao parent; membros de Agent Teams podem se comunicar diretamente entre si
- Task list compartilhada (JSON no filesystem); membros pegam tarefas autonomamente
- Boa pratica: plan first (barato), parallelize second (caro mas rapido)
- Modelo de custo: cada teammate ocupa uma context window inteira, ou seja, mais agents = mais tokens

**4. As tres estrategias de Context Engineering do Manus**

- Reduce: compactar stale results -> summarize quando o ganho da compaction comeca a diminuir
- Offload: armazenar tool results no filesystem, recuperar sob demanda com glob/grep; empurrar acoes para a camada sandbox (tool set pequeno + Bash)
- Isolate: o objetivo principal de um sub-agent e isolar contexto (nao dividir trabalho); para tarefa simples, repassar so a instrucao; para tarefa complexa, repassar o contexto completo

**5. Defesa contra a Bitter Lesson**

O alerta "Peak" do Manus: o harness do agent pode limitar os ganhos de performance do modelo.

- Tatica: rodar evals em modelos de forca diferente; se um modelo mais forte nao gera ganho de performance, o harness esta segurando o sistema
- Boris Cherny, criador do Claude Code, tambem foi influenciado pela Bitter Lesson e mantem o Claude Code com pouca opiniao
- Desde o lancamento em 2025-03, o Manus ja foi reescrito 5 vezes

### Comparacao com o framework atual

| Paper / pratica do mercado | Estado do framework | Lacuna |
|---|---|---|
| Initializer Agent monta o ambiente na primeira vez | Ralph Loop usa o mesmo prompt em toda iteracao | 🔴 ausente |
| Tool result compaction | A cada iteracao temos uma instancia nova do CLI (isolamento natural), mas sem compaction dentro de uma iteracao | 🔴 ausente |
| Cada session valida o ambiente rodando testes primeiro | build_prompt nao tem instrucao de "validar o ambiente primeiro" | 🟡 ausente |
| Feature list em JSON | Checklist em Markdown (ja teve episode com falso positivo) | 🟡 otimizavel |
| Comunicacao direta entre agents (Teams) | Strategy D e fire-and-forget | 🟡 atualizavel |
| Defesa contra a Bitter Lesson | Hooks com restricoes rigidas, sem modo relax | 🟢 baixa prioridade |
| Avanco incremental + commit + progress | ✅ Ralph Loop + progress.md + findings.md | coberto |
| Hook enforcement | ✅ PreToolUse/PostToolUse/Stop | a frente do paper |
| Circuit breaker | ✅ parada automatica apos 3 rounds sem progresso | a frente do paper |
| Revisao multiangulo do plano | ✅ 4 reviewers em paralelo | a frente do paper |
| Auto-evolucao do knowledge | ✅ episodes + self-reflect | a frente do paper |
| Security hooks | ✅ varias camadas de bloqueio de seguranca | a frente do paper |

### Prioridade das sugestoes de otimizacao

| Prioridade | Direcao | Ganho esperado | Dificuldade |
|---|---|---|---|
| P0 | Instrucao de Tool Result Compaction (alterar prompt) | evita queda de QI dentro de uma iteracao | baixa |
| P0 | Cada iteracao valida o ambiente rodando testes primeiro (alterar prompt) | evita empilhar bugs sobre ambiente quebrado | baixa |
| P1 | Modo Initializer Agent (alterar ralph_loop.py) | primeira iteracao mais eficiente | media |
| P1 | Suporte a Agent Teams (depende de feature experimental do CC) | comunicacao entre agents em paralelo | media |
| P2 | Separar checklist em JSON (alterar plan.py + hooks) | elimina falsos positivos do parse de Markdown | media |
| P2 | Defesa contra a Bitter Lesson (adicionar variavel de ambiente) | framework nao limita o avanco do modelo | baixa |
