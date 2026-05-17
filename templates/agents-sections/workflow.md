<!-- BEGIN OMK WORKFLOW -->
## Workflow
- Explore → Plan → Code (primeiro pesquise, depois planeje, depois codifique)
- Tarefas complexas: comece por interview, nao assuma
- **Tarefas que envolvem alteracoes em varios arquivos devem ler `skills/planning/SKILL.md` e seguir o fluxo completo a risca:**
  1. Phase 0: Deep Understanding (pesquisa + perguntas)
  2. Phase 1: Write Plan (escreva em `docs/plans/`, com `## Tasks` + `## Checklist` + `## Review` obrigatorios)
  3. Phase 1.5: Plan Review (dispatch de 4 reviewer subagents em paralelo)
  4. Phase 2: Execute (apos confirmacao do usuario, execute via ralph loop)
  5. **Proibido pular o reviewer dispatch da Phase 1.5; proibido fazer review do seu proprio plan**

## Skill Routing

| Cenario | Skill | Como acionar | Como carregar |
|------|-------|---------|---------|
| Planejamento/design | planning | comando `@plan` | pre-carregado |
| Execucao do plan | planning + ralph loop | comando `@execute` | pre-carregado |
| Code Review | reviewing | comando `@review` | pre-carregado |
| Debug | debugging | injecao automatica via rules.md | sob demanda |
| Pesquisa | research | comando `@research` | sob demanda |
| Verificacao antes de concluir | verification | Stop hook automatico | sob demanda |
| Encerramento de branch | finishing | apos planning concluido | sob demanda |
| Correcao/aprendizado | self-reflect | deteccao via context-enrichment | sob demanda |
| Descobrir skills | find-skills | quando o usuario perguntar | sob demanda |

## Knowledge Retrieval
- Question → knowledge/INDEX.md → topic indexes → source docs
- Hook 🔎 resultados em primeiro lugar - quando houver recall do OV, use primeiro o conteudo do recall; se nao bastar, complemente com find/grep. Proibido contornar o OV e ir direto ao filesystem
<!-- END OMK WORKFLOW -->

