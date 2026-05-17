# Investigação: {title}

> Criada em: {date} | Status: 🔴 Investigando / 🟡 Parcial / 🟢 Resolvida

## Problem Statement
<!-- descreva o problema em uma frase, no maximo 3 linhas -->

## Status Overview
<!-- ⚡ area de atualizacao por sobrescrita, atualize sempre que houver progresso real -->

**Status**: 🔴 Em investigacao
**Confianca na causa raiz**: ⬜ Nao confirmada

| # | Sub-problema | Status | Causa raiz | Fix |
|---|--------|------|------|------|
| 1 | {descricao do sub-problema} | ⬜ Nao investigado | - | - |

**Investigation Tree:**
```
{问题}
├── {排查方向 1} → ⬜
└── {排查方向 2} → ⬜
```

**Proximo passo**: {acao concreta}
**Bloqueios**: nenhum

## Evidence Table

### 🔒 L0 - Machine Facts (nao podem ser invalidados)
<!-- saida de comando, analise de codigo, resposta de API, resultado de experimento -->
<!-- APPEND-ONLY: so adiciona, nao apaga, nao edita -->

| # | Hora | Evidencia | Fonte | Relacionado |
|---|------|------|------|------|
| F1 | {time} | {fact} | {command/code/api} | {sub-problemas relacionados} |

### 👤 L1 - Human Observations (precisa de justificativa solida para questionar)
<!-- operacoes e fenomenos reportados pelo usuario -->
<!-- APPEND-ONLY -->

| # | Hora | Observacao | Reportado por | Confianca |
|---|------|------|--------|--------|
| H1 | {time} | {observation} | {who} | alto/medio/baixo |

### 🤖 L2 - Agent Inferences (podem ser revisadas)
<!-- deducoes, hipoteses e conclusoes de analise feitas pela IA -->
<!-- pode marcar ~~struck~~ para indicar refutado, mas nao apague o texto original -->

| # | Hora | Inferencia | Base | Status |
|---|------|------|------|------|
| I1 | {time} | {inference} | baseado em F1, H1 | ✅ valida / ❌ refutada |

## Decision Log
<!-- APPEND-ONLY: registre a evolucao das decisoes para nao refazer caminhos ja descartados -->

| # | Hora | Decisao | Justificativa | Status |
|---|------|------|------|------|
| D1 | {time} | {decision} | {rationale} | ✅ adotada / ❌ substituida por D{n} |

## Experiment Log
<!-- APPEND-ONLY: registro estruturado de experimentos -->

#### EXP-001: {nome do experimento}
- **Hora**: {time}
- **Ambiente**: {browser/OS/endpoint}
- **Operacao**: {comando ou passos especificos}
- **Esperado**: {expected}
- **Real**: {actual}
- **Nivel de evidencia**: 🔒 L0
- **Conclusao**: {conclusion}
- **Relacionado**: → F{n}, D{n}

## Ruled Out
<!-- APPEND-ONLY: direcoes ja descartadas, evita que uma nova session as reinvestigue -->

| # | Direcao | Motivo da exclusao | Base |
|---|------|---------|------|
| R1 | {direction} | {why ruled out} | EXP-{n} / F{n} |

## Timeline
<!-- APPEND-ONLY: linha do tempo da investigacao -->

### {date} {time} - {milestone}
{descricao detalhada}
