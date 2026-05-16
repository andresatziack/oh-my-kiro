---
name: mermaid-diagrams
description: Comprehensive guide for creating software diagrams using Mermaid syntax. Use when users need to create, visualize, or document software through diagrams including class diagrams (domain modeling, object-oriented design), sequence diagrams (application flows, API interactions, code execution), flowcharts (processes, algorithms, user journeys), entity relationship diagrams (database schemas), C4 architecture diagrams (system context, containers, components), state diagrams, git graphs, pie charts, gantt charts, or any other diagram type. Triggers include requests to "diagram", "visualize", "model", "map out", "show the flow", or when explaining system architecture, database design, code structure, or user/application flows.
---

# Diagramação com Mermaid

Crie diagramas profissionais de software usando a sintaxe baseada em texto do Mermaid. O Mermaid renderiza diagramas a partir de definições simples em texto, tornando os diagramas versionáveis, fáceis de atualizar e mantíveis junto do código.

## Estrutura Básica da Sintaxe

Todos os diagramas Mermaid seguem este padrão:

```mermaid
diagramType
  definition content
```

**Princípios principais:**
- A primeira linha declara o tipo de diagrama (ex.: `classDiagram`, `sequenceDiagram`, `flowchart`)
- Use `%%` para comentários
- Quebras de linha e indentação melhoram a legibilidade, mas não são obrigatórias
- Palavras desconhecidas quebram diagramas; parâmetros falham em silêncio

## Guia de Seleção do Tipo de Diagrama

**Escolha o tipo de diagrama correto:**

1. **Class Diagrams** - modelagem de domínio, design OOP, relacionamentos entre entidades
   - Documentação de domain-driven design
   - Estruturas de classes orientadas a objeto
   - Relacionamentos e dependências entre entidades

2. **Sequence Diagrams** - interações temporais, fluxos de mensagens
   - Fluxos de request/response de API
   - Fluxos de autenticação de usuário
   - Interações entre componentes do sistema
   - Sequências de chamadas de método

3. **Flowcharts** - processos, algoritmos, árvores de decisão
   - Jornadas de usuário e workflows
   - Processos de negócio
   - Lógica de algoritmo
   - Pipelines de deploy

4. **Entity Relationship Diagrams (ERD)** - schemas de banco de dados
   - Relacionamentos entre tabelas
   - Modelagem de dados
   - Design de schema

5. **C4 Diagrams** - arquitetura de software em múltiplos níveis
   - System Context (sistemas e usuários)
   - Container (aplicações, bancos, serviços)
   - Component (estrutura interna)
   - Code (nível de classe/interface)

6. **State Diagrams** - máquinas de estado, estados de ciclo de vida
7. **Git Graphs** - estratégias de branching de controle de versão
8. **Gantt Charts** - linhas do tempo de projeto, agendamento
9. **Pie/Bar Charts** - visualização de dados

Para diretrizes detalhadas e exemplos, consulte [reference.md](./reference.md).
