---
name: documentation-lookup
description: "Fetch current library/framework documentation via Context7. Trigger when user asks about libraries, frameworks, API references, code examples, setup/configuration, or mentions specific frameworks like React, Vue, Next.js, Prisma, Supabase, Express, Tailwind, Django, FastAPI, Spring Boot, etc. Also trigger when user says 'how to use', 'API docs', 'latest syntax', or needs code involving third-party packages."
---

## Trigger Examples
- "Next.js 15 的 middleware 怎么配？"
- "show me the Prisma query syntax for upsert"
- "React 19 有什么新 API？"
- "how do I set up Supabase auth?"
- "Tailwind 的 grid 怎么用？"

Quando o usuário perguntar sobre libraries, frameworks ou precisar de exemplos de código, use o Context7 para buscar documentação atual em vez de confiar em training data.

## Quando usar esta Skill

Ative esta skill quando o usuário:

- Fizer perguntas de setup ou configuração ("How do I configure Next.js middleware?")
- Pedir código envolvendo libraries ("Write a Prisma query for...")
- Precisar de referências de API ("What are the Supabase auth methods?")
- Mencionar frameworks específicos (React, Vue, Svelte, Express, Tailwind, etc.)

## Como buscar documentação

### Step 1: Resolver o Library ID

Chame `resolve-library-id` com:

- `libraryName`: O nome da library extraído da pergunta do usuário
- `query`: A pergunta completa do usuário (melhora o ranking de relevância)

### Step 2: Selecionar a melhor correspondência

Entre os resultados da resolução, escolha com base em:

- Correspondência exata ou mais próxima ao que o usuário pediu
- Pontuações de benchmark mais altas indicam melhor qualidade da documentação
- Se o usuário mencionou uma versão (por exemplo, "React 19"), prefira IDs específicos da versão

### Step 3: Buscar a documentação

Chame `query-docs` com:

- `libraryId`: O Context7 library ID escolhido (por exemplo, `/vercel/next.js`)
- `query`: A pergunta específica do usuário

### Step 4: Usar a documentação

Incorpore a documentação obtida em sua resposta:

- Responda à pergunta do usuário usando informações atuais e corretas
- Inclua exemplos de código relevantes da documentação
- Cite a versão da library quando relevante

## Diretrizes

- **Seja específico**: Passe a pergunta completa do usuário como query para obter melhores resultados
- **Atenção à versão**: Quando o usuário mencionar versões ("Next.js 15", "React 19"), use IDs de library específicos da versão se disponíveis na etapa de resolução
- **Prefira fontes oficiais**: Quando houver várias correspondências, prefira pacotes oficiais/primários a forks da comunidade
