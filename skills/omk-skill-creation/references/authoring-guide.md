# Referência de Authoring de Skill

> Material de referência detalhado para criação de skills. Leia on demand, não pré-carregue.

## Fontes

Esta referência sintetiza boas práticas de:
- Anthropic oficial: "Skill authoring best practices" (platform.claude.com/docs)
- Anthropic oficial: "A complete guide to building skills for Claude" (2026-01-29)
- Anthropic oficial: meta-skill skill-creator (melhorada em 2026-03)
- TDS: "How to Build a Production-Ready Claude Code Skill", de Hajime Takeda (2026-03-16)
- Comunidade: skill guide do shareuhack.com, skill guide do yu-wenhao.com

## Description Writing Deep Dive

### Por que descriptions importam tanto

Na inicialização, apenas name + description (~100 tokens por skill) são carregados. O agent usa
apenas esses metadados para decidir se carrega o SKILL.md completo. Se a description for vaga,
a skill nunca dispara, não importa quão bom seja o corpo.

Comportamento do agent: por padrão NÃO dispara. Ele prefere pular uma skill a disparar incorretamente.
Testes mostram que descriptions vagas derrubam a precisão de auto-trigger para ~55%.

### Fórmula da description

```
[What it does in one sentence]. [Trigger when user says "keyword1", "keyword2",
"keyword3", or describes scenario X]. [Also trigger when implicit condition Y].
```

### Constraints
- name: ≤64 chars, lowercase + hyphens, sem "anthropic"/"claude"
- description: ≤1024 chars, não vazio, sem tags XML
- Sempre em terceira pessoa ("Processes X", não "I help you")

### Estratégia de keywords-trigger

1. Comece pelos casos de uso, o que os usuários vão de fato dizer?
2. Inclua keywords em inglês e em chinês se for bilíngue
3. Inclua sinônimos (por exemplo, "review" + "check" + "audit")
4. Inclua triggers implícitos (tipos de arquivo, contextos)
5. Mais frases-trigger > menos (o agent sub-dispara, não sobre-dispara)

## Three-Layer Loading (Disclosure progressivo)

| Layer | O quê | Quando carrega | Custo em tokens |
|-------|------|-------------|------------|
| L1: Metadata | name + description | Sempre (startup) | ~100 tokens/skill |
| L2: Corpo do SKILL.md | Instruções completas | Quando o agent considera relevante | Variável |
| L3: references/ + scripts/ | Arquivos de apoio | On demand | Zero até serem lidos |

Orçamento de contexto: skills recebem ~2% da janela de contexto, cap de fallback de 16.000 chars.
Verifique com o comando `/context` se as skills estão sendo excluídas.

## Detalhes dos patterns

### Pattern A: Prompt-Only
Apenas SKILL.md com instruções em markdown. Sem scripts.
Melhor para: brand guidelines, padrões de código, checklists de review, estilo de escrita.
Quando: o julgamento do agent sozinho é suficiente.

### Pattern B: Prompt + Scripts
SKILL.md + código executável em scripts/.
Melhor para: transformação de dados, processamento de PDF/Excel, geração de templates, relatórios numéricos.
Scripts executam sem entrar no contexto, economizando tokens e garantindo precisão.
Suportados: Python, JavaScript/Node.js, Bash.

### Pattern C: Skill + MCP/Subagent
Chama MCP servers ou inicia subagents de dentro do workflow.
Melhor para: workflows envolvendo serviços externos (criar issue → branch → fix → PR).
Mais peças móveis = mais debugging. Fique confortável com A/B primeiro.

## Exemplos de Freedom Level

### Liberdade baixa (operações frágeis)
```markdown
## Database Migration
Run exactly this script:
```bash
python scripts/migrate.py --verify --backup
```
Do not modify the command or add additional flags.
```

### Liberdade média (existe um padrão preferido)
```markdown
## Generate Report
Use this template and customize as needed:
```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data → generate output → optionally include visualizations
```
```

### Liberdade alta (múltiplas abordagens válidas)
```markdown
## Code Review Process
1. Analyze code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability
4. Verify adherence to project conventions
```

## Patterns comuns

### Template Pattern
Forneça templates de formato de saída. Estrito para APIs/dados, flexível para prosa.

### Examples Pattern
Pares input/output ensinam melhor que descrições:
```
Input: Added user authentication with JWT tokens
Output: feat(auth): implement JWT-based authentication
```

### Conditional Workflow Pattern
```
1. Determine type:
   Creating new? → Follow "Creation workflow"
   Editing existing? → Follow "Editing workflow"
```

### Feedback Loop Pattern
Run → validate → fix → validate again. Melhora muito a qualidade do output.

### HITL (Human-in-the-Loop) Pattern
Pause após cada stage e aguarde a confirmação do usuário antes de prosseguir.
A experiência mostra que pipelines totalmente automatizados produzem qualidade menor que
pipelines revisados por humano em cada stage.

### File-Based Communication Pattern
Cada skill escreve a saída em um arquivo. A próxima skill lê o mesmo arquivo.
Mais confiável que passar dados pelo contexto (o contexto desaparece no fim da sessão).

## Desenvolvimento orientado por avaliação

1. Identifique gaps: rode o agent em tasks SEM a skill. Documente as falhas.
2. Crie avaliações: 3+ cenários testando esses gaps.
3. Estabeleça baseline: meça a performance sem a skill.
4. Escreva instruções mínimas: o suficiente para passar nas avaliações.
5. Itere: execute as avaliações, compare com a baseline e refine.

## Boas práticas para scripts

- Trate erros explicitamente, não empurre para o agent
- Documente todas as constantes (sem magic numbers)
- Liste pacotes obrigatórios no SKILL.md
- Deixe a intenção de execução clara: "Run X" (executar) vs. "See X" (ler como referência)
- Prefira scripts para operações determinísticas em vez de pedir que o agent gere o código
- Use forward slashes em paths (mesmo no Windows)

## Ciclo de vida da skill

Skills não são write-once-and-forget:
1. v1: acerte primeiro o workflow na conversa, depois extraia
2. v2-v3: corrija issues descobertos no uso diário
3. Em andamento: review mensal, a skill ainda corresponde à realidade?
4. Aposentadoria: remova ou unifique skills pouco usadas

> "Good workflows are grown, not designed.", guia do skill-creator da Anthropic
