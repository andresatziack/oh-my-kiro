Você DEVE seguir esta sequência exata. @debug é um pipeline de depuração totalmente automatizado, sem confirmação do usuário entre estágios. O objetivo é a análise sistemática da causa raiz, não tentativa e erro.

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

## Estágio 0: Verificação de retomada de sessão

Antes de iniciar qualquer investigação, verifique se há documentos de investigação existentes:

1. Liste `docs/investigations/`, procurando arquivos que correspondam ao tópico do bug atual
2. Se existir um documento correspondente:
   - Leia a seção **Status Overview** para entender o estado atual
   - Leia a seção **Ruled Out** para evitar reinvestigar caminhos sem saída
   - Leia o **Decision Log** para entender decisões anteriores
   - Retome a partir do último estado registrado, NÃO recomece do zero
3. Se nenhum documento correspondente existir:
   - Crie `docs/investigations/{date}-{topic}.md` usando `skills/omk-debugging/investigation-template.md` como template
   - Preencha o Problem Statement com o relato do bug do usuário

**Protocolo de retomada de sessão:** Toda nova sessão DEVE consultar `docs/investigations/` primeiro. O documento de investigação é a única fonte da verdade para continuidade entre sessões.

## Estágio 1: Triagem e contexto

1. Leia `knowledge/episodes.md`, verifique se esse padrão de bug já ocorreu antes
2. Construa o Architectural Context em torno do bug:
   - `generate_codebase_overview` → estrutura dos módulos
   - `find_references` no(s) símbolo(s) central(is) do bug → todos os callers
   - `get_document_symbols` no(s) arquivo(s) do bug → estrutura interna
3. Classifique o tipo de falha:

| Categoria | Sinal |
|----------|--------|
| Logic/Semantic | Teste falha, saída errada |
| Environment/Config | Funciona localmente, falha em outro lugar |
| Concurrency/Timing | Intermitente |
| Invalid Invocation | Erro de schema, resposta 400 |
| Under-specified Intent | Precisa de mais contexto |

4. Escreva o resumo de triagem no documento de investigação (`docs/investigations/{date}-{topic}.md`):
   - Preencha **Problem Statement**
   - Adicione entradas iniciais à **Evidence Table** (fatos L0 vindos dos diagnostics)
   - Construa a **Investigation Tree** inicial com os ramos de topo
   - Atualize **Status Overview** com os resultados da triagem e os próximos passos

## Estágio 2: Investigação da causa raiz

Siga `skills/omk-debugging/SKILL.md` Phase 1 + `references/root-cause-protocol.md`.

Sequência de tools, use as tools de LSP, NÃO grep:

| Step | Ação |
|------|--------|
| 1 | `get_diagnostics` no(s) arquivo(s) com falha |
| 2 | `search_symbols` → `goto_definition` → `find_references` nos símbolos envolvidos |
| 3 | Leia mensagens de erro / stack traces por completo |
| 4 | Reproduza o bug de forma consistente |
| 5 | Verifique alterações recentes (`git diff`, commits recentes) |

Produza **Diagnostic Evidence** antes de prosseguir:
```
Diagnostic Evidence:
- failure_type: [category]
- get_diagnostics: [errors found]
- search_symbols: [symbols located]
- find_references: [callers/usage sites]
- key_variables:
  - var_name / expected / actual / location
- Root cause hypothesis: [conclusion]
```

**Gate:** Sem Diagnostic Evidence, NÃO prossiga para o Estágio 3.

**Apos concluir:** Atualize o documento de investigação, adicione as evidências de diagnóstico L0 à Evidence Table e atualize o Status Overview com as descobertas e próximos passos.

## Estágio 3: Análise de padrões e hipótese

Siga `skills/omk-debugging/SKILL.md` Phase 2-3 + `references/pattern-analysis.md`.

1. Encontre exemplos funcionais de código semelhante na codebase
2. Compare o que funciona vs. o que está quebrado, liste TODAS as diferenças
3. Formule UMA hipótese: "X é a causa raiz porque Y"
4. Teste com a MENOR alteração possível, uma variável de cada vez
5. Se a hipótese falhar → formule uma NOVA hipótese, não acumule fixes

Anexe ao scratch:
```
- Hypothesis: <statement>
- Test: <what minimal change was tried>
- Result: confirmed | rejected → <next hypothesis if rejected>
```

**Gate:** A hipótese deve ser confirmada antes de prosseguir para o Estágio 4.

**Apos concluir:** Atualize o documento de investigação, registre a hipótese e os resultados do teste no Decision Log, adicione experimentos ao Experiment Log e atualize o Status Overview.

## Estágio 4: Fix e Verify

Siga `skills/omk-debugging/SKILL.md` Phase 4 + `references/implementation-fix.md`.

1. `get_diagnostics` → registre baseline
2. Crie um caso de teste falhando (se possível)
3. Implemente UM ÚNICO fix abordando a causa raiz, sem alterações empacotadas
4. `get_diagnostics` → zero novos diagnostics, ou reverta
5. Rode os testes → verifique o fix, sem regressões
6. Auto-explique: causa raiz → lógica do fix → efeitos colaterais (verifique contra o Architectural Context)

**Regra de 3 strikes:** Se 3 tentativas de fix falharem → PARE, questione a arquitetura, discuta com o usuário.

**Apos concluir:** Atualize o documento de investigação, atualize o Status Overview para o estado final (🟢 Resolved ou 🟡 Partial) e registre a decisão final no Decision Log.

## Estágio 5: Reporte

Gere o relatório final a partir do documento de investigação (`docs/investigations/{date}-{topic}.md`):

```markdown
## Debug Report
- **Bug:** <description>
- **Root Cause:** <what was actually wrong>
- **Fix:** <what was changed and why>
- **Verification:** <test results>
- **Side Effects:** <none | list>
```

Se o bug for um padrão novo, anexe um resumo de uma linha em `knowledge/episodes.md`.

## Sinais de alerta - rollback automático para o Estágio 2

Se em QUALQUER estágio você se pegar:
- Propondo fixes sem Diagnostic Evidence
- Usando grep em vez das tools de LSP para navegação no código
- Dizendo "just try X"
- Empilhando várias alterações de uma vez
- Pulando reprodução

→ **PARE. Volte ao Estágio 2.** Carregue `references/red-flags.md` para a lista completa.

---
User's bug report:
{content}
