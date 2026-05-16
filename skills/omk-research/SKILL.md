---
name: omk-research
description: "Multi-level research: built-in knowledge → web search → Tavily deep research API. Trigger when user says 'research', 'investigate', 'find out', 'compare', 'what is', 'how does X work', 'competitive analysis', 'market research', '@research', or needs information beyond the current codebase and knowledge base."
---

## Trigger Examples
- "@research AutoMQ vs Confluent 对比"
- "帮我调研一下这个库怎么用"
- "find out how competitors handle this"
- "what's the best practice for X in 2026?"
- "compare these three approaches"

# Skill de Pesquisa, busca em múltiplos níveis

## Estratégia de níveis de busca

Sempre use o nível mais baixo que consegue responder à pergunta:

| Nível | Tool | Caso de uso | Custo |
|-------|------|----------|------|
| 0 | Conhecimento embutido | Conceitos comuns, básicos | Grátis |
| 1 | `web_search` | Verificação rápida, queries simples | Grátis |
| 2 | Tavily Research API | Pesquisa profunda, análise competitiva | Créditos da API |

**Regra**: Se o Level 0 ou 1 já responde, não use Level 2.

**Não precisa de pesquisa**: Conhecimento comum, já está em `knowledge/`, ou respondível pelo conhecimento embutido.

## Level 2: Tavily Research API

### Pré-requisitos

Pegue sua API key em https://tavily.com (1000 créditos gratuitos por mês)

Defina a env var:
```bash
export TAVILY_API_KEY="tvly-your-key-here"
```

Ou adicione na config do agent:
```json
{
  "env": {
    "TAVILY_API_KEY": "tvly-your-key-here"
  }
}
```

### Uso

```bash
./scripts/research.sh '{"input": "your research query"}' [output_file]

# Quick research
./scripts/research.sh '{"input": "quantum computing trends"}'

# Deep research
./scripts/research.sh '{"input": "AI agents comparison", "model": "pro"}'

# Save to file
./scripts/research.sh '{"input": "market analysis", "model": "pro"}' ./report.md
```

### Seleção de modelo

| Modelo | Caso de uso | Velocidade |
|-------|----------|-------|
| `mini` | Tópico único, focado | ~30s |
| `pro` | Multi-ângulo, abrangente | ~60-120s |
| `auto` | A API escolhe pela complexidade | Varia |

**Regra prática**: "what does X do?" → mini. "X vs Y vs Z" → pro.

### Saída estruturada

```bash
./scripts/research.sh '{
  "input": "fintech startups 2025",
  "model": "pro",
  "output_schema": {
    "properties": {
      "summary": {"type": "string", "description": "Executive summary"},
      "companies": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["summary"]
  }
}'
```

### Formatos de citação

Suportados: `numbered` (default), `mla`, `apa`, `chicago`

```bash
./scripts/research.sh '{"input": "climate impacts", "citation_format": "apa"}'
```

## Checkpoint pós-pesquisa 沉淀

Após concluir a pesquisa, antes de escrever findings ou recomendações:

**Validação Socrática (obrigatória para cada recomendação/gap/otimização):**
1. Esse problema existe de fato na codebase atual? Verifique soluções existentes primeiro.
2. O fix proposto é viável em todas as plataformas alvo (Kiro + CC)? Verifique constraints.
3. O benefício supera o custo de manutenção?

Se alguma resposta for "não" → descarte essa recomendação. Não a inclua nos findings.

**Em seguida, persista:**
1. Registre os findings validados em `docs/plans/findings.md` (se estiver trabalhando em um plan)
2. Se os findings revelarem padrões reutilizáveis → escreva em `knowledge/episodes.md`
3. Cite as fontes com URLs, sem referências alucinadas
