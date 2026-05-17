# OV: sincronizacao automatica e reforco de recall

**Objetivo:** garantir que mudancas em arquivos de knowledge feitas por qualquer caminho (fs_write, execute_bash, edicao externa, git pull) sejam automaticamente sincronizadas para o OV, e que falhas de recall gerem alerta explicito em vez de fallback silencioso.
**Não-Objetivos:** nao alterar o proprio OV daemon (ov-daemon.py); nao alterar o formato de dados do OV; nao adicionar comandos novos ao OV.
**Arquitetura:** reforco em tres camadas. (1) session-init checa o daemon no cold start e sincroniza incrementalmente os arquivos de knowledge para o OV; (2) o hook post-bash detecta mudancas em arquivos de knowledge depois de cada execute_bash e sincroniza; (3) na Layer 4 do context-enrichment, falhas do OV emitem alerta.
**Tech Stack:** Bash (hooks), Python3 (deteccao de inicializacao do ov-daemon)
**Diretório de Trabalho:** `.`

## Review

**Round 1 (4 reviewers):**
- Goal Alignment: APPROVE
- Verify Correctness: REQUEST CHANGES (false positive — rejected)
- Completeness: REQUEST CHANGES → fixed (stronger Task 2 verify, added silent-failure test)
- Technical Feasibility: subagent failed

**Round 2 (2 reviewers, fixed angles only):**
- Goal Alignment: APPROVE
- Verify Correctness: APPROVE

**Final Verdict: APPROVE**

## Tarefas

### Tarefa 1: cold start do OV em session-init + sincronizacao incremental

**Arquivos:**
- Modify: `hooks/feedback/session-init.sh`
- Lib: `hooks/_lib/ov-init.sh` (ja existe, basta dar source)

**What to implement:**

No final de session-init.sh (antes de `touch "$LESSONS_FLAG"`), adicionar o bloco de inicializacao do OV:

1. dar source em ov-init.sh e chamar ov_init
2. se o OV daemon nao estiver rodando (socket inexistente), tentar iniciar em background com `python3 scripts/ov-daemon.py &` e aguardar ate 3 segundos pelo socket
3. quando o OV estiver disponivel, iterar sobre `knowledge/*.md` e chamar `ov_add` para cada arquivo, fazendo a sincronizacao incremental
4. se o OV permanecer indisponivel (overlay nao configurado ou daemon falhou ao subir), emitir uma linha de alerta

**Verificação:** `grep -q 'ov_add' hooks/feedback/session-init.sh && grep -q 'ov-daemon' hooks/feedback/session-init.sh`

### Tarefa 2: hook post-bash detecta mudancas em arquivos de knowledge

**Arquivos:**
- Modify: `hooks/feedback/post-bash.sh`
- Lib: `hooks/_lib/ov-init.sh` (ja existe)

**What to implement:**

Em post-bash.sh, depois da gravacao do verify log, incluir o bloco de sincronizacao com o OV:

1. checar se a string do comando referencia caminhos `knowledge/`; quando referenciar, chamar `ov_add` para cada arquivo .md correspondente
2. falhar em silencio (quando o OV estiver indisponivel, nao bloquear a execucao do bash)

**Verificação:** `grep -q 'ov_add' hooks/feedback/post-bash.sh`

### Tarefa 3: alerta de falha de recall no context-enrichment

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`

**What to implement:**

Alterar o bloco da Layer 4: quando o overlay tiver openviking configurado mas `ov_init` falhar, emitir a linha de alerta `⚠️ OV unavailable — knowledge semantic recall degraded. Run: python3 scripts/ov-daemon.py &` em vez de pular silenciosamente.

**Verificação:** `grep -q 'OV unavailable' hooks/feedback/context-enrichment.sh`

### Tarefa 4: testes

**Arquivos:**
- Modify: `tests/test_ov_capture.py` (adiciona teste de sincronizacao OV em post-bash)
- Modify: `tests/test_ov_recall.py` (adiciona teste de alerta quando OV esta indisponivel)

**What to implement:**

1. `test_post_bash_indexes_knowledge_changes`: faz mock do socket do OV, simula o input do hook quando execute_bash grava em arquivo de knowledge, e verifica que `ov_add` foi chamado
2. `test_post_bash_silent_when_ov_down`: quando o OV esta indisponivel, post-bash ainda termina normalmente (exit 0), sem erro
3. `test_enrichment_warns_when_ov_down`: overlay tem openviking configurado mas o socket nao existe; verificar que a stdout contem `⚠️ OV unavailable`

**Verificação:** `python3 -m pytest tests/test_ov_capture.py tests/test_ov_recall.py -v`

## Checklist

- [x] session-init inicia o OV daemon automaticamente quando ele nao esta rodando | `bash -c 'source hooks/_lib/ov-init.sh && type ov_init' && grep -q 'ov-daemon' hooks/feedback/session-init.sh`
- [x] session-init sincroniza incrementalmente knowledge/*.md para o OV | `grep -q 'ov_add' hooks/feedback/session-init.sh`
- [x] post-bash detecta mudancas em arquivos de knowledge e sincroniza com o OV | `grep -q 'knowledge/' hooks/feedback/post-bash.sh && grep -A3 'knowledge/' hooks/feedback/post-bash.sh | grep -q 'ov_add'`
- [x] context-enrichment emite alerta quando o OV falha | `grep -q 'OV unavailable' hooks/feedback/context-enrichment.sh`
- [x] todos os hooks com sintaxe correta | `bash -n hooks/feedback/session-init.sh && bash -n hooks/feedback/post-bash.sh && bash -n hooks/feedback/context-enrichment.sh`
- [x] novos testes passam | `python3 -m pytest tests/test_ov_capture.py tests/test_ov_recall.py -v`
- [x] nao usa o comando timeout (que nao existe no macOS) | `! grep -rn '\btimeout\b' hooks/feedback/session-init.sh hooks/feedback/post-bash.sh hooks/feedback/context-enrichment.sh`

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

