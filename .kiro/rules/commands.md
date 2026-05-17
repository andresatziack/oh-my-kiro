# Custom Commands

## @lint - Verificação de Saúde

Quando o usuário disser `@lint`, execute a verificação de saúde das instruções:

```bash
wc -l CLAUDE.md  # or AGENTS.md
grep -n "don't\|must\|never\|always\|禁止\|必须" CLAUDE.md
```

Gere um relatório de saúde com:
- Contagem atual de linhas / orçamento de 200 linhas
- Regras que poderiam ser aplicadas via código
- Sugestões de migração para enforcement.md

## @compact - Compactar Instruções

Dispara o fluxo de compactação:
1. Identificar regras de baixa frequência → mover para reference.md
2. Identificar regras aplicáveis via código → criar enforcement
3. Mesclar regras duplicadas
4. Apertar a redação

## Checklist de Revisão (Antes de Adicionar à Layer 2)

| Verificação | Pergunta | Se Sim → |
|-------------|----------|----------|
| **Aplicável via código** | Isso pode virar linter/test/hook? | Escreva código, não prosa |
| **Alta frequência** | É necessário em toda conversa? | Adicione à Layer 2 |
| **Não duplicada** | Já está coberta? | Mescle ou atualize |
| **Verificável** | Como checar conformidade? | Defina a verificação |
| **Concisa** | Pode ser mais curta? | Aperte primeiro |

## Language Matching

O agent deve responder no idioma do usuario. Se o usuario falar portugues, responda em portugues; se falar ingles, responda em ingles; se falar chines, responda em chines.
