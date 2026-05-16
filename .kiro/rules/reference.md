# Camada de Referência Sob Demanda

> Regras detalhadas e materiais, carregados apenas quando necessários.

## Templates

### Template de Deep Interview

Antes de montar um plan, pergunte:
```
1. [Goal] What's the desired outcome? Success criteria?
2. [Context] What triggered this need?
3. [Constraints] Time, budget, technical limits?
4. [Reference] Any good examples to follow?
5. [Priority] What's essential vs. nice-to-have?
```

### Checklist de Compound Interest

| Verificação | Trigger | Alvo de Atualização |
|-------------|---------|---------------------|
| Novo conhecimento? | Usuário fornece contexto | `knowledge/` |
| Dado estruturado extraído? | De arquivos/research | `-structured.md` |
| Plan/proposta final? | Conclusão da tarefa | `plans/` |
| Novo diretório? | Criado durante a tarefa | Criar `INDEX.md` |

### Detecção de Comportamento Repetido

Ao detectar operações repetidas ≥3 vezes:
```
💡 Compound Interest Reminder: I've noticed you've [done X] [N] times.
Suggest creating:
- [ ] Template → `templates/[name].md`
- [ ] Tool → `tools/[name].sh`
Create now?
```

## Tratamento de Scripts Longos

```python
# ❌ Wrong: Long inline scripts
executeBash("python -c 'import xxx; ... very long code ...'")

# ✅ Right: Write to file first
fsWrite("script.py", "import xxx\n...")
executeBash("python script.py")
```

## Execução de Comandos Longos

```bash
command &
PID=$!
for i in {1..6}; do
    sleep 10
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "Command completed"; break
    fi
    echo "[$((i*10))s] Still running..."
done
wait $PID 2>/dev/null
```
