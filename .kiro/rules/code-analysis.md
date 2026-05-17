# Code Analysis

Em cenarios de leitura, analise e navegacao de codigo, use de preferencia ferramentas LSP (search_symbols, find_references, goto_definition, get_hover etc.) em vez de busca linha a linha com grep/fs_read.

Motivo: o LSP fornece analise no nivel semantico (tipos, cadeia de referencias, salto para definicao); grep faz apenas correspondencia de texto e tende a perder ou casar errado.

Aplicacao:
- Encontrar definicao/referencias de simbolos -> search_symbols + find_references
- Entender tipo/assinatura -> get_hover
- Visao geral da estrutura do arquivo -> get_document_symbols
- Compreensao de arquitetura -> generate_codebase_overview
- Debug -> get_diagnostics e a ferramenta preferencial; depois de obter erros e avisos do compilador, use search_symbols + find_references para localizar a causa raiz

Cold start:
- Ao entrar em um projeto denso em codigo (com .py/.ts/.rs etc.), execute primeiro initialize_workspace para inicializar o LSP e garantir que as demais ferramentas funcionem

Fase de exploracao:
- Antes de mergulhar em arquivos especificos, use generate_codebase_overview para obter a visao geral do projeto

Busca estruturada:
- Para procurar padroes de codigo (por exemplo, todo tratamento de erro, todas as chamadas de API) -> pattern_search, em vez de grep
- pattern_search e baseado em AST e casa estrutura, nao texto

Transformacao segura de codigo:
- Substituicao estrutural de codigo -> pattern_rewrite (rode dry_run para preview), substituindo sed
- Motivacao: sed em JSON/codigo quebra a estrutura facilmente (o hook block-sed-json.sh intercepta)

Cuidados com pattern em python:
- `def $FUNC($$$):` nao funciona; escreva como `def $FUNC($$$ARGS): $$$BODY`
- O pattern ast-grep para python precisa incluir um placeholder para o corpo da funcao

Excecoes:
- Buscar texto em comentarios/strings -> grep
- Ler arquivos que nao sao codigo (markdown, config) -> fs_read

