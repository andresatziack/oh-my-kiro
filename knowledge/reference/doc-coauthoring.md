---
name: doc-coauthoring
description: Guide users through a structured workflow for co-authoring documentation. Use when user wants to write documentation, proposals, technical specs, decision docs, or similar structured content. This workflow helps users efficiently transfer context, refine content through iteration, and verify the doc works for readers. Trigger when user mentions writing docs, creating proposals, drafting specs, or similar documentation tasks.
---

# Workflow de Co-Autoria de Documentação

Esta skill fornece um workflow estruturado para guiar usuários na criação colaborativa de documentos. Atue como um guia ativo, conduzindo o usuário pelas três etapas: Coleta de Contexto, Refinamento e Estrutura, e Reader Testing.

## Quando Oferecer Este Workflow

**Condições de gatilho:**
- Usuário menciona escrita de documentação: "write a doc", "draft a proposal", "create a spec", "write up"
- Usuário menciona tipos específicos de doc: "PRD", "design doc", "decision doc", "RFC"
- Usuário parece estar começando uma tarefa substancial de escrita

**Oferta inicial:**
Ofereça ao usuário um workflow estruturado para co-autoria do documento. Explique as três etapas:

1. **Coleta de Contexto**: o usuário fornece todo o contexto relevante enquanto o Claude faz perguntas de esclarecimento
2. **Refinamento e Estrutura**: construa cada seção iterativamente por meio de brainstorming e edição
3. **Reader Testing**: teste o doc com um Claude limpo (sem contexto) para detectar pontos cegos antes que outras pessoas leiam

Explique que essa abordagem ajuda a garantir que o doc funcione bem quando outras pessoas o lerem (inclusive quando colarem o conteúdo no Claude). Pergunte se a pessoa quer experimentar este workflow ou prefere trabalhar de forma livre.

Se o usuário recusar, trabalhe de forma livre. Se aceitar, vá para a Etapa 1.

## Etapa 1: Coleta de Contexto

**Objetivo:** fechar a lacuna entre o que o usuário sabe e o que o Claude sabe, permitindo orientação inteligente nas próximas etapas.

### Perguntas Iniciais

Comece pedindo ao usuário um meta-contexto sobre o documento:

1. Que tipo de documento é este? (ex.: technical spec, decision doc, proposal)
2. Quem é o público primário?
3. Qual é o impacto desejado quando alguém ler isto?
4. Há um template ou formato específico a seguir?
5. Alguma outra restrição ou contexto a considerar?

Avise que a pessoa pode responder em forma resumida ou despejar a informação da maneira que funcionar melhor para ela.

**Se o usuário fornecer um template ou mencionar um tipo de doc:**
- Pergunte se a pessoa tem um documento de template para compartilhar
- Se ela enviar um link para um documento compartilhado, use a integração apropriada para buscar
- Se ela enviar um arquivo, leia o arquivo

**Se o usuário mencionar a edição de um documento compartilhado existente:**
- Use a integração apropriada para ler o estado atual
- Verifique se há imagens sem alt-text
- Se houver imagens sem alt-text, explique que, quando outras pessoas usarem o Claude para entender o doc, o Claude não conseguirá vê-las. Pergunte se a pessoa quer gerar alt-text. Em caso afirmativo, peça que ela cole cada imagem no chat para gerar um alt-text descritivo.

### Despejo de Informações

Depois que as perguntas iniciais forem respondidas, incentive o usuário a despejar todo o contexto que tem. Solicite informações como:
- Background do projeto/problema
- Discussões de equipe relacionadas ou documentos compartilhados
- Por que soluções alternativas não estão sendo usadas
- Contexto organizacional (dinâmica de time, incidentes passados, política)

Para passos detalhados de workflow e templates, consulte [reference.md](./reference.md).
