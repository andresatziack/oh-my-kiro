# Descobertas

## Padrões da Codebase

- **Estrutura de build_prompt:** Retorno de uma única f-string. Novas seções de prompt são anexadas antes do `"""` de fechamento. Todo conteúdo dinâmico usa interpolação de f-string com variáveis computadas acima do return.
- **Padrão de teste:** Os testes importam `build_prompt` e `PlanFile` diretamente, criam um plan mínimo em `tmp_path`, chamam `build_prompt()` e fazem assert sobre o conteúdo da string. Sem necessidade de subprocess para testes de prompt.
- **Timing do hook de plan:** O hook verify-before-checkoff exige que o comando verify seja a chamada `execute_bash` mais recente antes do `str_replace` que marca `- [x]`. Executá-lo antes e fazer outras chamadas de tool no meio aciona o bloqueio.

- **Falhas pré-existentes de teste:** 4 testes em test_ralph_loop.py falham antes de qualquer mudança: test_detect_claude_cli, test_no_cli_found, test_parse_config_defaults, test_claude_cmd_has_no_session_persistence. Todos relacionados a detecção de CLI e defaults de config - provavelmente de uma migração recente do kiro-cli que atualizou o comportamento de detect_cli sem atualizar os testes.
