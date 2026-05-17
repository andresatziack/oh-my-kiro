# Template de Removal e Plan de Iteração

## Níveis de prioridade

- [ ] **P0**: remoção imediata necessária (risco de segurança, custo significativo, bloqueando outro trabalho)
- [ ] **P1**: remover na sprint atual
- [ ] **P2**: backlog / próxima iteração

---

## Seguro para remover agora

### Item: [Name/Description]

| Campo | Detalhes |
|-------|---------|
| **Localização** | `path/to/file.ts:line` |
| **Justificativa** | Por que isso deve ser removido |
| **Evidência** | Sem uso (sem referências), feature flag morto, API deprecated |
| **Impacto** | Nenhum / baixo, sem consumers ativos |
| **Steps de deleção** | 1. Remover código 2. Remover testes 3. Remover config |
| **Verificação** | Rodar testes, checar runtime errors, monitorar logs |

---

## Adiar remoção (plan obrigatório)

### Item: [Name/Description]

| Campo | Detalhes |
|-------|---------|
| **Localização** | `path/to/file.ts:line` |
| **Por que adiar** | Consumers ativos, precisa de migration, sign-off de stakeholder |
| **Pré-condições** | Feature flag desligado por 2 semanas, telemetria mostrando 0 uso |
| **Breaking changes** | Liste quaisquer alterações de API/contrato |
| **Plan de migração** | Steps para os consumers migrarem |
| **Timeline** | Data alvo ou sprint |
| **Owner** | Pessoa/time responsável |
| **Validação** | Métricas para confirmar remoção segura (taxas de erro, contagens de uso) |
| **Plan de rollback** | Como restaurar em caso de problemas |

---

## Checklist antes da remoção

- [ ] Buscou todas as referências na codebase (`rg`, `grep`)
- [ ] Verificou uso dinâmico/via reflection
- [ ] Verificou que não há consumers externos (APIs, SDKs, docs)
- [ ] Telemetria de feature flag revisada (se aplicável)
- [ ] Testes atualizados/removidos
- [ ] Documentação atualizada
- [ ] Time notificado (se for código compartilhado)
