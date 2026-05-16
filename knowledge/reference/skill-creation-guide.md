---
name: skill-creator
description: Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.
license: Complete terms in LICENSE.txt
---

# Skill Creator

Esta skill fornece orientação para criar skills efetivas.

## Sobre Skills

Skills são pacotes modulares e auto-contidos que estendem as capacidades do Claude fornecendo
conhecimento especializado, workflows e ferramentas. Pense nelas como "guias de onboarding" para domínios
ou tarefas específicas: elas transformam o Claude de um agent de propósito geral em um agent especializado
equipado com conhecimento procedural que nenhum modelo consegue possuir totalmente.

### O Que as Skills Fornecem

1. Workflows especializados - procedimentos multi-etapa para domínios específicos
2. Integrações com ferramentas - instruções para trabalhar com formatos de arquivo ou APIs específicas
3. Expertise de domínio - conhecimento específico de empresa, schemas, lógica de negócio
4. Recursos empacotados - scripts, referências e assets para tarefas complexas e repetitivas

## Princípios Centrais

### Conciso é Essencial

A janela de contexto é um bem público. As skills compartilham a janela de contexto com tudo o mais que o Claude precisa: system prompt, histórico da conversa, metadados de outras skills e o request real do usuário.

**Premissa padrão: o Claude já é muito inteligente.** Adicione apenas contexto que o Claude ainda não tem. Questione cada informação: "O Claude realmente precisa desta explicação?" e "Este parágrafo justifica seu custo em tokens?"

Prefira exemplos concisos a explicações verbosas.

### Ajuste Graus de Liberdade Apropriados

Combine o nível de especificidade com a fragilidade e variabilidade da tarefa:

**Alta liberdade (instruções em texto)**: use quando múltiplas abordagens são válidas, decisões dependem do contexto, ou heurísticas guiam a abordagem.

**Liberdade média (pseudocódigo ou scripts com parâmetros)**: use quando existe um padrão preferido, alguma variação é aceitável, ou a configuração afeta o comportamento.

**Baixa liberdade (scripts específicos, poucos parâmetros)**: use quando as operações são frágeis e propensas a erro, a consistência é crítica, ou uma sequência específica precisa ser seguida.

Pense no Claude como alguém explorando um caminho: uma ponte estreita com penhascos exige guardrails específicos (baixa liberdade), enquanto um campo aberto permite muitas rotas (alta liberdade).

### Anatomia de uma Skill

Toda skill consiste em um arquivo SKILL.md obrigatório e recursos empacotados opcionais:

```
skill-name/
├── SKILL.md (required)
│   ├── YAML frontmatter metadata (required)
│   │   ├── name: (required)
│   │   └── description: (required)
│   └── Markdown instructions (required)
└── Bundled Resources (optional)
    ├── scripts/          - Executable code (Python/Bash/etc.)
    ├── references/       - Documentation intended to be loaded into context as needed

For detailed skill creation guidelines, templates, and examples, see [reference.md](./reference.md).
