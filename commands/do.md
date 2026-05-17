Comando leve para tasks pequenas (< 1 hora). Sem arquivo de plan, sem dispatch de review. Evita drift de contexto em interações de múltiplos turnos.

## Estágio 1: Scratchpad (OBRIGATÓRIO, mesmo se a task parecer trivial)

Antes de QUALQUER alteração de código, escreva um scratchpad em `/tmp/task-scratch.md`:

```markdown
## Task: <one-line description>
- Files: <list files to read/modify, discovered via LSP>
- Constraint: <key constraints or gotchas>
- Verify: <how to verify success>
```

Steps de descoberta (silenciosos, sem saída para o usuário):
1. `search_symbols` / `find_references` / `get_diagnostics` para identificar todos os arquivos afetados
2. Leia as seções relevantes de cada arquivo afetado (NÃO os arquivos inteiros, use offsets de linha)
3. Atualize o scratchpad com a lista real de arquivos e descobertas-chave

## Estágio 2: Executar

Faça as alterações seguindo `skills/omk-coding/SKILL.md` Phase 1-4.

**Regra do âncora de contexto:** Após CADA modificação de código, anexe uma linha de status ao scratchpad:
```
- [done] modified hooks/feedback/context-enrichment.sh L37-41: expanded CN keywords
- [done] created symlink commands/auto.md → oh-my-kiro
- [blocked] test fails: grep pattern doesn't match "超时"
```

## Estágio 3: Verify

1. Execute o método de verify do scratchpad
2. Releia o scratchpad para confirmar que todos os itens foram tratados
3. Reporte o resultado ao usuário

## Recuperação em múltiplos turnos

Se a conversa já tiver passado de 3 turnos nesta task:
1. PARE e releia `/tmp/task-scratch.md`
2. Compare o estado atual vs. o scratchpad, identifique o drift
3. Se houver drift, declare o que mudou e corrija o curso

---
User's task:
(A próxima mensagem do usuário é a task. Se esta for a primeira mensagem após @do ter sido invocado e nenhuma task aparecer acima, aguarde a próxima mensagem do usuário, ela conterá a task. NÃO pergunte "o que você quer fazer?", o usuário já sabe que precisa fornecer a entrada após @do.)
