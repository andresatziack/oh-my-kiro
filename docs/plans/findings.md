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

### 核心发现

**1. Anthropic 论文的两阶段 Agent 架构**

论文核心创新：Initializer Agent（首次 session 搭建环境）+ Coding Agent（后续 session 增量推进）。

- Initializer Agent 职责：写 feature list（JSON 格式）、写 init.sh、写 progress.txt、做初始 git commit
- Coding Agent 职责：每次 session 先读 progress + git log + 跑基础测试，然后只做一个 feature，完成后 commit + 更新 progress
- 关键发现：JSON 格式的 feature list 比 Markdown 更不容易被 agent 篡改
- 关键发现：不先验证环境就开始新 feature 会让已有 bug 更严重

**2. Context Rot 与 Compaction**

Anthropic context engineering 论文核心观点：context 是有限资源，随 token 增加注意力预算被稀释（n² pairwise relationships）。

- Manus 实践：tool result 有 full/compact 两种表示，旧 result 自动替换为 compact（只保留路径引用）
- Anthropic 平台：context editing 功能自动清除 stale tool call results
- 研究发现：直接移除旧 tool result（不做 LLM summarization）在 observation-heavy 场景下效果等同或更好
- 关键原则："find the smallest possible set of high-signal tokens that maximize the likelihood of desired outcome"

**3. Sub-agent 架构演进 → Agent Teams**

Claude Code 2026 年初推出 Agent Teams（Swarm Mode）：

- 7 个原语：TeamCreate, TaskCreate, TaskUpdate, TaskList, Task(team_name), SendMessage, TeamDelete
- 关键区别：subagent 只能报告回 parent，Agent Teams 成员可以互相直接通信
- 共享 task list（文件系统上的 JSON），自主认领任务
- 最佳实践：plan first（便宜），parallelize second（贵但快）
- 成本模型：每个 teammate 是完整 context window，更多 agent = 更多 token

**4. Manus 的 Context Engineering 三策略**

- Reduce：compact stale results → summarize when compaction 收益递减
- Offload：tool result 存文件系统，用 glob/grep 按需检索；action 推到 sandbox 层（小 tool set + Bash）
- Isolate：sub-agent 主要目的是隔离 context（不是分工）；简单任务只传指令，复杂任务传完整 context

**5. Bitter Lesson 防护**

Manus 的 Peak 警告：agent harness 可能限制模型性能提升。

- 做法：跨模型强度运行 eval，如果更强模型没带来性能提升，说明 harness 在拖后腿
- Claude Code 创始人 Boris Cherny 也受 Bitter Lesson 影响，保持 Claude Code 不 opinionated
- Manus 自 2025-03 发布以来已重构 5 次

### 与现有框架的对照分析

| 论文/行业实践 | 框架现状 | 差距 |
|---|---|---|
| Initializer Agent 首次搭建环境 | Ralph Loop 每次 iteration 用相同 prompt | 🔴 缺少 |
| Tool result compaction | 每次 iteration 新 CLI 实例（天然隔离），但单次内无 compaction | 🔴 缺少 |
| 每次 session 先跑测试验证环境 | build_prompt 没有"先验证环境"指令 | 🟡 缺少 |
| Feature list 用 JSON | Checklist 用 Markdown（已有误判 episode） | 🟡 可优化 |
| Agent 间直接通信（Teams） | Strategy D 是 fire-and-forget | 🟡 可升级 |
| Bitter Lesson 防护 | Hook 约束较刚性，无松弛模式 | 🟢 低优先 |
| 增量推进 + commit + progress | ✅ Ralph Loop + progress.md + findings.md | 已覆盖 |
| Hook 强制执行 | ✅ PreToolUse/PostToolUse/Stop | 领先论文 |
| Circuit breaker | ✅ 3 轮无进展自动停止 | 领先论文 |
| Plan review 多角度审查 | ✅ 4 reviewer 并行 | 领先论文 |
| Knowledge 自进化 | ✅ episodes + self-reflect | 领先论文 |
| Security hooks | ✅ 多层安全拦截 | 领先论文 |

### 优化建议优先级

| 优先级 | 方向 | 预期收益 | 实现难度 |
|---|---|---|---|
| P0 | Tool Result Compaction 指令（改 prompt） | 单次 iteration 内防降智 | 低 |
| P0 | 每次 iteration 先跑测试验证环境（改 prompt） | 防止在坏环境上叠加 bug | 低 |
| P1 | Initializer Agent 模式（改 ralph_loop.py） | 第一个 iteration 更高效 | 中 |
| P1 | Agent Teams 支持（需 CC 实验特性） | 并行 agent 间通信 | 中 |
| P2 | Checklist JSON 分离（改 plan.py + hooks） | 消除 Markdown 解析误判 | 中 |
| P2 | Bitter Lesson 防护（加环境变量） | 框架不限制模型进步 | 低 |
