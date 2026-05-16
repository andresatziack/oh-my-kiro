# Descobertas do Plano do Evaluator

## Padrões da Codebase

- **Padrão de arquivo de comando:** Comandos em `commands/` são arquivos markdown com estrutura Step 1/2/3. Veja `commands/review.md` como padrão de referência (resolver alvo -> coletar contexto -> dispatch de subagent -> reportar).
- **Nomenclatura do diretório de skills:** Skills usam o prefixo `omk-` (por exemplo, `skills/omk-debugging/`), não nomes simples.
- **Dispatch de subagent:** Use `use_subagent` com até 4 entradas paralelas. Cada uma recebe uma persona, instruções específicas e requisitos de saída estruturada.
- **Enforcement de hook:** O hook que marca o checklist exige que o comando verify exato seja executado via `execute_bash` (não envolto em echo) imediatamente antes da chamada `str_replace`.
- **Padrão de config:** Toda leitura de env var em `main()` deve passar pelo dataclass `Config` + `parse_config()`. O teste `test_main_has_no_inline_env_reads` faz esse enforcement - adicionar um novo `os.environ.get` em `main()` quebra o CI.
- **Defaults de env de teste:** O helper de teste `run_ralph` define `RALPH_SKIP_*=1` para todos os estágios skip-able. Novos estágios precisam adicionar sua env var de skip a esse conjunto default para evitar que testes não relacionados travem.

## Decisões de Design

- O prompt do evaluator usa 7 pontos de enforcement REJECTED (4 regras de tabela vazia por subagent + 3 na agregação) para prevenir avaliações rubber-stamp.
- Canary questions são por subagent e exigem leitura efetiva do código fonte para serem respondidas - previne que evaluators gerem feedback genérico sem ler o diff.

