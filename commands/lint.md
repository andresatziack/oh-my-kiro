Execute estas verificações de saúde e reporte os resultados:

## 1. Contagem de linhas do CLAUDE.md
```bash
LINES=$(wc -l < CLAUDE.md | tr -d ' ')
[ "$LINES" -lt 500 ] && echo "✅ CLAUDE.md: $LINES lines (< 500)" || echo "❌ CLAUDE.md: $LINES lines (≥ 500 — trim it)"
```

## 2. Tamanhos dos arquivos em .claude/rules/
```bash
for f in .claude/rules/*.md; do
  LINES=$(wc -l < "$f" | tr -d ' ')
  NAME=$(basename "$f")
  [ "$LINES" -lt 200 ] && echo "✅ $NAME: $LINES lines" || echo "❌ $NAME: $LINES lines (≥ 200)"
done
```

## 3. Headers de Layer
```bash
for f in .claude/rules/*.md; do
  NAME=$(basename "$f")
  grep -q 'Layer: Agent Rule' "$f" && echo "✅ $NAME has header" || echo "❌ $NAME missing Layer header"
done
```

## 4. Sincronização CLAUDE.md / AGENTS.md
```bash
diff CLAUDE.md AGENTS.md && echo "✅ CLAUDE.md and AGENTS.md in sync" || echo "❌ CLAUDE.md and AGENTS.md out of sync — run: cp CLAUDE.md AGENTS.md"
```

## 5. Verificação de duplicação
```bash
DUPS=0
for f in .claude/rules/*.md; do
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    echo "$line" | grep -q '^#' && continue
    if grep -qF "$line" knowledge/rules.md 2>/dev/null; then
      echo "⚠️ Duplicate: $line"
      DUPS=$((DUPS + 1))
    fi
  done < "$f"
done
[ "$DUPS" -eq 0 ] && echo "✅ No verbatim duplication" || echo "❌ $DUPS duplicated lines between .claude/rules/ and knowledge/rules.md"
```

Reporte todos os resultados. Se houver algum ❌, liste os fixes recomendados.
