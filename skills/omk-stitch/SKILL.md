---
name: omk-stitch
triggers: "stitch|design.?to.?code|UI.?design|visual.?compare|screen.*code|figma.*stitch|设计稿|设计.*代码|视觉.*对比|design.?md|design.?system|shadcn.*stitch|redesign"
description: >
  Google Stitch design-to-code workflow with design system management.
  Trigger when user mentions Stitch, design-to-code, UI design, visual comparison,
  design.md, design system, ShadCN conversion, redesign from screenshot, or wants
  to pull designs from Stitch into local code. Also trigger when user says
  '做个页面', 'build a landing page', '用 Stitch 设计', 'convert design',
  'export from Stitch', '设计系统', or uploads wireframes/screenshots for UI generation.
metadata:
  pattern: tool-wrapper
  domain: design
---

## Trigger Examples
- "Pull my Stitch designs into code"
- "monte uma landing page com o Stitch"
- "use o estilo desse screenshot no meu site"
- "Export design.md from my Stitch project"
- "Convert Stitch design to ShadCN components"

# Skill de integração com o Google Stitch

## Conceito central: design.md

O design system do Stitch é capturado em um arquivo `design.md`, cores, fontes, temas, estilos de componente. Esse arquivo é:
- **Otimizado para agents**, usa linguagem direcionada que os agents entendem melhor do que CSS bruto
- **Transferível**, dê o arquivo para Claude Code, Cursor ou qualquer agent e eles reproduzem o estilo perfeitamente
- **Auto-criado**, o Stitch gera um para cada projeto, mesmo que você não peça

**Workflow padrão**: comece sempre estabelecendo um design.md, depois construa páginas em cima dele.

## MCP Server

Pacote da comunidade: [davideast/stitch-mcp](https://github.com/davideast/stitch-mcp)
npm: `@_davideast/stitch-mcp`

## Setup

### Pré-requisitos
- Google Cloud CLI (`gcloud`) instalado
- Um projeto GCP com a Stitch API habilitada

### Autenticação (OAuth, API Key NÃO é suportada)

```bash
gcloud auth login
gcloud auth application-default login
gcloud config set project <YOUR_PROJECT_ID>
gcloud auth application-default set-quota-project <YOUR_PROJECT_ID>
gcloud beta services mcp enable stitch.googleapis.com --project=<YOUR_PROJECT_ID>
```

### Config do MCP

Adicione na config do seu MCP client (por exemplo, `.kiro/settings/mcp.json`):
```json
{
  "stitch": {
    "command": "npx",
    "args": ["@_davideast/stitch-mcp", "proxy"],
    "env": {
      "STITCH_USE_SYSTEM_GCLOUD": "1",
      "GOOGLE_CLOUD_PROJECT": "<YOUR_PROJECT_ID>"
    }
  }
}
```

CRÍTICO: É preciso usar o modo `proxy` + `STITCH_USE_SYSTEM_GCLOUD=1`. O modo serverUrl direto é instável.

### Verificar setup

```bash
npx @_davideast/stitch-mcp doctor
```

Se o `doctor` der timeout no teste de API, verifique diretamente:
```bash
ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
curl -s -w "\nHTTP:%{http_code}" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "x-goog-user-project: <YOUR_PROJECT_ID>" \
  "https://stitch.googleapis.com/v1/projects"
```

## Tools de MCP

| Tool | Propósito |
|------|---------|
| `list_projects` | Lista todos os projetos do Stitch |
| `get_screen_code` | Obtém HTML/CSS de uma tela |
| `get_screen_image` | Obtém screenshot da tela (base64) |
| `build_site` | Mapeia telas para rotas, gera projeto Astro |

## Tools CLI (não-MCP)

```bash
npx @_davideast/stitch-mcp view --projects          # Browse projects
npx @_davideast/stitch-mcp serve -p <project-id>    # Local preview
npx @_davideast/stitch-mcp site -p <project-id>     # Generate Astro site
```

## Workflows

### Caminho A: Design do zero (padrão)

1. **Estabeleça o design system**, crie ou forneça um `design.md` no Stitch (auto-criado se não especificado)
2. **Gere telas**, faça prompts no Stitch com seus requisitos, ele constrói em cima do design system
3. **Puxe para o local**, `get_screen_code` → HTML/CSS, `get_screen_image` → screenshot
4. **Implemente**, converta para o framework alvo (Next.js/Astro/React)
5. **Verifique**, comparação visual (veja Phase: Verificação abaixo)

### Caminho B: Redesign a partir de referência

Use quando você tem um site/screenshot existente cujo estilo quer adotar (não copiar):

1. **Capture a referência**, screenshot da página inteira do site que você gosta (use GoFullPage ou similar)
2. **Redesign no Stitch**, faça upload do screenshot, o Stitch extrai a linguagem visual, padrões de componente e layout, e aplica ao SEU conteúdo
3. **Alternativa: importar via URL**, no painel de design system do Stitch, importe a partir de qualquer URL. O Stitch crawla o site e extrai tipografia + cores como design.md
4. **Refine**, faça upload de wireframes ou anote seções específicas para ajustar

### Caminho C: Build integrado por agent (Claude Code + Stitch)

Para builds end-to-end autônomos usando as skills oficiais de Stitch do Google:

1. **Enhanced Prompt**, converte prompts vagos do usuário em prompts otimizados para o Stitch (o Stitch depende de adjetivos para mood, não de descrições exatas)
2. **Stitch Loop**, loop autônomo de build usando Chrome DevTools, mantém prompt tracking entre stages
3. **React Components**, converte o HTML monolítico exportado pelo Stitch em componentes React modulares com validação

Ordem do workflow em `claude.md`:
```
Enhanced Prompt → Stitch Loop → React Component conversion
```

Requer Stitch MCP conectado. Veja o [repo das skills oficiais de Stitch do Google](https://github.com/nicepkg/stitch-skills) para instalação.

### Caminho D: Conversão para ShadCN UI

React/HTML cru do Stitch não tem interações. Use ShadCN para componentes de qualidade de produção:

1. Conecte o ShadCN MCP
2. Use a skill ShadCN UI do Google para converter designs do Stitch em componentes ShadCN
3. Estenda com registries (por exemplo, glassmorphism, motion-primitives) para um feel premium
4. Especifique os registries em `claude.md` para que a conversão seja automática

## Phase: Verificação (inspirada no design-review do gstack)

Após a implementação, rode uma verificação multi-layer. O objetivo: pegar o que olho humano não pega.

### Layer 1: Screenshots em múltiplos viewports

Capture screenshots em 3 breakpoints para pegar issues de responsividade:

```bash
npx playwright screenshot --viewport-size=375,812 http://localhost:3000 impl-mobile.png
npx playwright screenshot --viewport-size=768,1024 http://localhost:3000 impl-tablet.png
npx playwright screenshot --viewport-size=1440,900 http://localhost:3000 impl-desktop.png
```

Verifique: overflow de texto, layout colapsando, elementos sobrepostos, conteúdo que não se adapta.

### Layer 2: Verificação de consistência do design system

Extraia os valores realmente renderizados na implementação e compare com o design.md:

```bash
# Extract fonts actually used (run in browser console or Playwright)
npx playwright evaluate http://localhost:3000 \
  "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).map(e => getComputedStyle(e).fontFamily))])"

# Extract color palette in use
npx playwright evaluate http://localhost:3000 \
  "JSON.stringify([...new Set([...document.querySelectorAll('*')].slice(0,500).flatMap(e => [getComputedStyle(e).color, getComputedStyle(e).backgroundColor]).filter(c => c !== 'rgba(0, 0, 0, 0)'))])"
```

Compare os valores extraídos contra os tokens do design.md. Sinalize desvios.

### Layer 3: Pixel diff vs. design

```bash
npx pixelmatch design.png impl-desktop.png diff.png 0.1
```

### Layer 4: Detecção de AI Slop

Verifique se a implementação tem estes 10 padrões gerados por IA (da blacklist do gstack):

1. Backgrounds em gradiente roxo/violeta como padrão
2. Grid de 3 colunas com ícone-em-círculo + título + descrição
3. Ícones em círculos coloridos como decoração de seção
4. `text-align: center` em tudo
5. border-radius arredondado uniforme em todos os elementos
6. Blobs decorativos, divisores SVG ondulados
7. Emoji como elemento de design
8. Borda esquerda colorida em cards
9. Copy genérica de hero ("Welcome to X", "Unlock the power of...")
10. Ritmo cookie-cutter de seções (hero → features → testimonials → pricing → CTA)

Se ≥3 padrões forem detectados, sinalize como "AI slop risk" e sugira correções específicas.

### Layer 5: Diff visual com IA

Alimente o LLM com design.png e impl-desktop.png para comparação. Pergunte especificamente:
- A hierarquia bate?
- As proporções de spacing foram preservadas?
- Há seções ou elementos faltando?

### Loop de refinamento

Após a verificação, itere:
1. Mostre ao usuário os screenshots + resultados de diff
2. O usuário fornece feedback
3. Aplique edits cirúrgicos (não regenere arquivos inteiros)
4. Verifique novamente
5. Repita até "done" (máximo 10 rodadas)

## Dicas de design.md

- **Template**: Pegue o template otimizado para agents no repo oficial das skills do Google
- **Transferência**: Dê o design.md para qualquer agent (Claude Code, Cursor) para um styling consistente
- **Extração**: Use a "design MD skill" do Google para extrair design.md de projetos Stitch existentes
- **Custom**: Crie seu próprio design.md com cores/fontes/temas e cole no painel de design system do Stitch

## Issues conhecidos

1. **API Key auth quebrada**, a Stitch API rejeita API keys, é preciso usar OAuth (confirmado em 2026-02 pela comunidade)
2. **Timeout de fetch do `doctor`**, dependente de rede, o teste direto via curl é mais confiável
3. **Billing não é exigido**, a Stitch API funciona em projetos sem billing habilitado
4. **Modo experimental sem Figma export**, apenas o modo Standard suporta Figma export
