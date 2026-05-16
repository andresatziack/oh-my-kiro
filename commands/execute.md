Executa um plan aprovado com a constraint dura do Ralph Loop. Paradas do agent não importam, o loop em bash continua até que todos os itens do checklist sejam concluídos.

## Step 1: Carregar o plan

Resolva qual plan executar:
1. Leia `docs/plans/.active`, se existir, use esse caminho
2. Se não existir, encontre o `docs/plans/*.md` modificado mais recentemente e escreva-o em `docs/plans/.active`
3. Se houver vários plans modificados na última hora, liste-os e peça ao usuário para escolher

Verifique se o plan tem o verdict APPROVE do reviewer. Se não estiver aprovado, diga ao usuário para rodar @plan primeiro.

## Step 1b: Detectar Work Dir

Verifique se o cabeçalho do plan contém `**Work Dir:**`:
```bash
WORK_DIR=$(grep -oE '^\*\*Work Dir:\*\*\s*.+' "$PLAN_FILE" | sed 's/^\*\*Work Dir:\*\*\s*//' | tr -d '[:space:]')
```

Se Work Dir estiver definido:
1. Resolva para um caminho absoluto relativo à raiz do projeto
2. Se o path não existir, crie um worktree (infira submodule e branch a partir do slug do plan)
3. Inicie o ralph loop com env vars de isolamento:
```bash
PLAN_POINTER_OVERRIDE=<plan_file_path> RALPH_WORK_DIR=<work_dir_abs> python3 scripts/ralph_loop.py
```

Se Work Dir estiver ausente, prossiga normalmente (compatível com versões anteriores).

## Step 2: Verificar o checklist

O plan DEVE conter uma seção `## Checklist` com pelo menos um item `- [ ]`. Se estiver faltando, PARE e diga ao usuário que o plan precisa de um checklist.

## Step 3: Iniciar o Ralph Loop

Rode em **foreground** (NUNCA use `nohup &`, você precisa ver o resumo de saída):
```bash
python3 scripts/ralph_loop.py
```

Esse script bash vai:
- Fazer loop até que todos os itens `- [ ]` virem `- [x]`
- Cada iteração inicia uma instância nova do Kiro CLI com contexto limpo
- Circuit breaker: sai se 3 rodadas consecutivas não tiverem progresso
- Paradas do agent estão ok, o loop reinicia uma nova instância
- Ao sair (sucesso ou falha), imprime um resumo completo no stdout

## Step 4: Reportar resultados

O script imprime um bloco de resumo ao sair. Use essa saída para reportar:
- Quantos itens do checklist concluídos vs. total
- Quaisquer itens `- [SKIP]` com motivos
- Leia skills/omk-finishing/SKILL.md para opções de merge/PR/cleanup
