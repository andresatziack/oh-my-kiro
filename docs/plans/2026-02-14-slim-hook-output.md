# Reduzir saida dos Hooks - liberar 32K para Auto-Compaction

**Objetivo:** Reduzir o consumo de tokens das saidas dos hooks para garantir que, quando o auto-compact disparar, o context ainda tenha >=32K disponiveis para a chamada da API de compaction.

**Causa Raiz:** O auto-compact do Kiro precisa de ~32K max_tokens quando dispara. Se o input ja passou de 168K (200K-32K), a propria requisicao de compact e rejeitada pela API (#1531). A saida dos hooks e a maior fonte controlavel de consumo de tokens.

## Plano de reducao

### 1. context-enrichment.sh (maior ponto de otimizacao)

**Hoje:** a cada input do usuario, injeta 4 linhas de lessons (~200 tokens x 20 rodadas = ~4000 tokens)
**Mudanca:** controlar via flag em /tmp para injetar apenas uma vez por session
**Economia:** ~3800 tokens em 20 rodadas

**Impacto:** lessons aparecem apenas uma vez no inicio da session. Se o agent violar regras mais tarde (por exemplo, sed em JSON), nao ha lembrete repetido. Mas block-sed-json.sh e bloqueio forte (exit 2), entao o lembrete das lessons e apenas uma rede de seguranca redundante. Impacto minimo.

### 2. inject-plan-context.sh (segundo maior ponto de otimizacao)

**Hoje:** a cada write injeta a secao inteira da checklist (~300 tokens x 60 writes = ~18000 tokens)
**Mudanca:** usar contador em /tmp; a cada 5 writes injeta a checklist completa, nas demais vezes apenas 1 linha "📋 N items remaining in plan"
**Economia:** ~14400 tokens em 20 rodadas (em 60 writes: 12 injecoes completas + 48 linhas curtas)

**Impacto:** o agent ve a checklist completa a cada 5 writes, evitando que o objetivo seja empurrado para fora da attention em sessions longas. Bem mais seguro do que remover por completo.

### 3. verify-completion.sh (sem mudanca)

Manter saida completa (contagem + itens nao concluidos especificos). Dispara apenas no stop; o custo em tokens e baixo, mas o agent precisa saber exatamente o que ficou faltando.

### 4. remind-update-progress.sh (ja bem enxuto)

**Hoje:** 1 linha de lembrete, ja pula *.md/*.json
**Mudanca:** sem alteracao
**Impacto:** nenhum

### 5. auto-test.sh (otimizacao pequena)

**Hoje:** em caso de falha imprime `tail -20` (no maximo 20 linhas)
**Mudanca:** em caso de falha imprime `tail -10` (no maximo 10 linhas)
**Economia:** ~500 tokens (acionada por condicao)

**Impacto:** as informacoes de falha de teste perdem 10 linhas. Em geral as 10 primeiras ja trazem o erro principal. Impacto minimo.

## Efeito estimado

| Hook | Hoje (20 rodadas) | Apos reducao (20 rodadas) | Economia |
|------|------------|-------------|------|
| context-enrichment lessons | ~4000 tokens | ~200 tokens | 3800 |
| inject-plan-context | ~18000 tokens | ~3600 tokens | 14400 |
| verify-completion | ~1000 tokens | ~1000 tokens | 0 |
| auto-test | ~2000 tokens | ~1000 tokens | 1000 |
| **Total** | **~25000** | **~5800** | **~19200** |

Economia de ~19K tokens. Somando a margem ja existente, sobra mais espaco para a compaction.

## Checklist
- [x] context-enrichment.sh: lessons sao injetadas uma unica vez por session via flag em /tmp
- [x] inject-plan-context.sh: contador em /tmp; injeta a checklist completa a cada 5 writes; nas demais vezes imprime apenas 1 linha com a contagem
- [x] auto-test.sh: trocar tail -20 por tail -10
- [x] apos as alteracoes, todos os scripts validados com bash -n sem erro de sintaxe

## Review

**VEREDITO: REQUEST CHANGES**

**Problemas críticos:**
1. ✅ **Checklist existe** com critérios de aceitação concretos `- [ ]`
2. ❌ **Erro de matemática de tokens**: alega 29K de espaço total, mas precisa de 32K para compaction
   - Atual: ~7K de margem + 22K economizados = 29K < 32K necessários
   - **Lacuna: 3K tokens ainda faltam**
3. ❌ **Avaliação de risco incompleta**: faltam análises sobre impacto no debugging quando os hooks fornecem menos contexto

**Preocupações específicas:**
- **Mudança em inject-plan-context.sh é DE ALTO RISCO**: remover a visibilidade do checklist durante sessões longas de coding pode fazer agentes perderem o rastro dos requisitos. A premissa "ralph-loop lê o plan no início" cai por terra se a sessão tiver >50 operações empurrando o checklist para fora da janela de context.
- **Mudança em verify-completion.sh reduz a eficiência de debugging**: quando builds falham, agentes precisam ver QUAIS itens estão incompletos, não só a contagem.

**Mudanças necessárias:**
1. Corrigir a matemática de tokens: encontrar 3K adicionais de economia ou reduzir o requisito de compaction
2. Adicionar mecanismo de fallback para inject-plan-context.sh (por exemplo, reinjetar o checklist a cada 10 operações)
3. Quantificar o impacto no debugging: quanto mais lenta será a resolução de issues sem a saída detalhada dos hooks?

**Sugestões:**
- Considerar redução progressiva: começar apenas pelo context-enrichment.sh (3.8K de economia), medir o impacto antes de mexer na injeção de plan
- Adicionar métricas para acompanhar com que frequência agentes releem planos após mudanças nos hooks
