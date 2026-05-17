---
name: writing-clearly-and-concisely
description: Use when writing prose humans will read—documentation, commit messages, error messages, explanations, reports, or UI text. Applies Strunk's timeless rules for clearer, stronger, more professional writing.
---

# Escrevendo com Clareza e Concisão

## Visão Geral

Escreva com clareza e força. Esta skill cobre o que fazer (Strunk) e o que evitar (padrões de IA).

## Quando Usar Esta Skill

Use esta skill sempre que escrever prosa para humanos:

- Documentação, arquivos README, explicações técnicas
- Commit messages, descrições de pull request
- Mensagens de erro, copy de UI, textos de ajuda, comentários
- Reports, resumos ou qualquer explicação
- Edição para melhorar a clareza

**Se você está escrevendo frases para um humano ler, use esta skill.**

## Estratégia em Contexto Limitado

Quando o contexto está apertado:

1. Escreva seu rascunho usando o próprio julgamento
2. Despache um subagent com seu rascunho e o arquivo da seção relevante
3. Peça ao subagent que faça o copy-edit e devolva a revisão

Carregar uma única seção (cerca de 1.000 a 4.500 tokens) em vez de tudo economiza um contexto significativo.

## Elements of Style

*The Elements of Style* (1918), de William Strunk Jr., ensina a escrever com clareza e a cortar sem dó.

### Regras

**Regras Elementares de Uso (Gramática/Pontuação)**:

1. Forme o possessivo singular adicionando 's
2. Use vírgula após cada termo de uma série, exceto o último
3. Cerque expressões parentéticas com vírgulas
4. Use vírgula antes da conjunção que introduz uma cláusula coordenada
5. Não una orações independentes apenas com vírgula
6. Não quebre frases ao meio
7. Frase participial no início se refere ao sujeito gramatical

**Princípios Elementares de Composição**:

8. Um parágrafo por tópico
9. Comece o parágrafo com uma frase-tópico
10. **Use voz ativa**
11. **Coloque afirmações na forma positiva**
12. **Use linguagem definida, específica e concreta**
13. **Omita palavras desnecessárias**
14. Evite sucessão de frases soltas
15. Expresse ideias coordenadas em forma similar
16. **Mantenha palavras relacionadas próximas**
17. Mantenha um único tempo verbal em resumos
18. **Coloque palavras enfáticas no fim da frase**

### Arquivos de Referência

As regras acima são resumos do texto original de Strunk. Para explicações completas com exemplos:

| Seção | Arquivo | ~Tokens |
|---------|------|---------|
| Gramática, pontuação, regras de vírgula | `02-elementary-rules-of-usage.md` | 2,500 |
| Estrutura de parágrafo, voz ativa, concisão | `03-elementary-principles-of-composition.md` | 4,500 |
| Headings, citações, formatação | `04-a-few-matters-of-form.md` | 1,000 |
| Escolha de palavras, erros comuns | `05-words-and-expressions-commonly-misused.md` | 4,000 |

**A maioria das tarefas precisa apenas de `03-elementary-principles-of-composition.md`** - cobre voz ativa, forma positiva, linguagem concreta e omissão de palavras desnecessárias.

## Padrões de Escrita de IA a Evitar

LLMs regridem para a média estatística e produzem prosa genérica e inflada. Evite:

- **Puffery:** pivotal, crucial, vital, testament, enduring legacy
- **Frases vazias com "-ing":** ensuring reliability, showcasing features, highlighting capabilities
- **Adjetivos promocionais:** groundbreaking, seamless, robust, cutting-edge
- **Vocabulário típico de IA, usado em excesso:** delve, leverage, multifaceted, foster, realm, tapestry
- **Excesso de formatação:** bullets em demasia, decorações com emoji, negrito a cada outra palavra

Seja específico, não grandioso. Diga o que realmente faz.

Para uma pesquisa abrangente sobre por que esses padrões surgem, consulte `signs-of-ai-writing.md`. Editores da Wikipedia desenvolveram este guia para detectar submissões geradas por IA, os padrões estão bem documentados e testados em campo.

## Conclusão

Escrevendo para humanos? Carregue a seção relevante de `elements-of-style/` e aplique as regras. Para a maioria das tarefas, `03-elementary-principles-of-composition.md` cobre o que mais importa.
