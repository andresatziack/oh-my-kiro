# Enforcement Layer (v3)

> Se puder ser garantido por código, não garanta com palavras.

## Registro de Hooks

| Regra | Caminho do Hook | Evento | Tipo |
|-------|-----------------|--------|------|
| Bloqueio de comando perigoso | `hooks/security/block-dangerous.sh` | preToolUse[bash] | block |
| Bloqueio de vazamento de segredo | `hooks/security/block-secrets.sh` | preToolUse[bash] | block |
| Bloqueio de sed/awk em JSON | `hooks/security/block-sed-json.sh` | preToolUse[bash] | block |
| Limite de workspace | `hooks/security/block-outside-workspace.sh` | preToolUse[bash,write] | block |
| Gate de pre-write (workflow + scan de injection + contexto do plan) | `hooks/gate/pre-write.sh` | preToolUse[write] | block + inject |
| Enforcer do ralph loop | `hooks/gate/enforce-ralph-loop.sh` | preToolUse[bash,write] | block |
| Enforcer OV-first | `hooks/gate/enforce-ov-first.sh` | preToolUse[bash] | block |
| Enforcer de diretório de trabalho | `hooks/gate/enforce-work-dir.sh` | preToolUse[write] | block |
| Exigência de regressão | `hooks/gate/require-regression.sh` | preToolUse[bash] | block |
| Gate de lint antes do push | `hooks/gate/require-lint-before-push.sh` | preToolUse[bash] | block |
| Feedback de post-write (lint + test + lembrete de progresso) | `hooks/feedback/post-write.sh` | postToolUse[write] | feedback |
| Log de execução de bash | `hooks/feedback/post-bash.sh` | postToolUse[bash] | feedback |
| Detecção de correção | `hooks/feedback/correction-detect.sh` | userPromptSubmit | inject |
| Inicialização de sessão (regras + limpeza) | `hooks/feedback/session-init.sh` | userPromptSubmit | inject |
| Enriquecimento de contexto (research + resume) | `hooks/feedback/context-enrichment.sh` | userPromptSubmit | inject |
| Verificação de conclusão | `hooks/feedback/verify-completion.sh` | stop | feedback |
| Captura automática (chamada por correction-detect.sh) | `hooks/feedback/auto-capture.sh` | shadow | inject |
| Relatório de saúde do KB (chamado por verify-completion.sh) | `hooks/feedback/kb-health-report.sh` | shadow | feedback |

## Camadas de Determinismo

| Camada | Mecanismo | Certeza |
|--------|-----------|---------|
| L0 Security | `hooks/security/*` (exit 2 = block) | 100% - hard block incondicional |
| L1 Commands | `@plan` `@execute` `@research` `@review` `@reflect` | 100% - disparado pelo usuário |
| L2 Gate | `hooks/gate/*` (exit 2 = block) | 100% - hard block |
| L3 Feedback | `hooks/feedback/*` (exit 0 = info only) | ~50% - apenas advisory |

## Geração de Configuração

Fonte única: `scripts/generate_configs.py`
Gera: `.kiro/settings.json` + `.kiro/agents/*.json` + `.kiro/agents/*.md`
