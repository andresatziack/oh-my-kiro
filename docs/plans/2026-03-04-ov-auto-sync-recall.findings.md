# OV Auto-Sync & Recall - Descobertas

## Padrões da Codebase

- **Sourcing de lib de hook:** `source "$(dirname "$0")/../_lib/<lib>.sh" 2>/dev/null || true` - sempre com fallback
- **Verificação de disponibilidade do OV:** `_ov_check_overlay` verifica `.omcc-overlay.json` para `knowledge_backend == openviking`; `ov_init` adicionalmente verifica socket + health
- **Compat com macOS:** Sem comando `timeout` disponível - use `sleep` em loop
- **Tratamento de erro em hooks:** Hooks não devem bloquear em falhas do OV - sempre `|| true` em chamadas ov
- **Guard de session-init:** Usa o arquivo `$LESSONS_FLAG` para rodar uma vez por sessão; código novo vai antes de `touch "$LESSONS_FLAG"`
