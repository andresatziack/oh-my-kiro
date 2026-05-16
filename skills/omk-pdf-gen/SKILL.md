---
name: omk-pdf-gen
description: >
  Generate professional PDF documents with correct CJK (Chinese/Japanese/Korean) rendering.
  Trigger when user says 'generate PDF', 'create PDF', 'export PDF', '生成 PDF', '导出 PDF',
  '做个 PDF', 'make a PDF', or when any task requires producing a PDF file.
  Also trigger when user mentions PDF formatting issues, garbled text, or font problems.
---

# Skill de Geração de PDF

## Trigger Examples
- "帮我生成一个报价 PDF"
- "把这个内容导出成 PDF"
- "PDF 中文乱码怎么办"
- "generate a comparison PDF for this customer"
- "create a budget proposal PDF"

## Abordagem: HTML + weasyprint

Use o pipeline **HTML + CSS → weasyprint**. NÃO use reportlab para documentos com texto CJK.

Por quê:
- As CID fonts do reportlab (STSong-Light) têm cobertura incompleta de glifos, símbolos como `•` viram lixo (ex.: "煉")
- O reportlab não consegue ler fontes TTC protegidas pelo SIP do macOS (PingFang etc.)
- A API `canvas` do reportlab exige posicionamento manual por coordenadas, frágil e feio
- O weasyprint usa o fontconfig do sistema, resolução de fontes correta de saída

## Workflow

### Step 1: Escreva a string HTML em Python

```python
HTML = """\
<!DOCTYPE html>
<html lang="zh">
<head><meta charset="utf-8">
<style>
@page { size: A4; margin: 2cm 2.2cm; }
body { font-family: "Hiragino Sans GB", "Heiti SC", "Noto Sans CJK SC", sans-serif; ... }
</style></head>
<body>...</body></html>
"""
```

### Step 2: Escreva em HTML temporário, converta e limpe

```python
import subprocess, os
html_tmp = output_path.replace('.pdf', '.html')
with open(html_tmp, 'w', encoding='utf-8') as f:
    f.write(HTML)
subprocess.run(['weasyprint', html_tmp, output_path], check=True)
os.remove(html_tmp)
```

## Regras de fontes (críticas)

| Plataforma | CSS font-family | Notas |
|----------|----------------|-------|
| macOS | `"Hiragino Sans GB", "Heiti SC"` | Verificado via `fc-list :lang=zh` |
| Linux | `"Noto Sans CJK SC", "WenQuanYi Micro Hei"` | Instale `fonts-noto-cjk` se faltar |
| Fallback | `sans-serif` | Sempre inclua como último recurso |

**Nunca use estes no CSS do weasyprint:**
- `-apple-system`, o weasyprint não entende aliases de fonte do Apple system
- `"PingFang SC"`, o fontconfig frequentemente não consegue resolver, mesmo com macOS tendo a fonte
- `"STSong-Light"`, nome de CID font, não é uma family real para CSS

**Antes de gerar**, verifique se há fontes CJK disponíveis:
```bash
fc-list :lang=zh family | head -10
```

## Boas práticas de styling

Use elementos HTML padrão, o weasyprint os trata bem:

- `<table>` com CSS `border-collapse: collapse` para tabelas de dados
- `<ul>/<li>` para listas (sem precisar de símbolos manuais)
- `<h1>-<h3>` para headings
- `<hr>` para divisores
- CSS `@page` para margens e tamanho da página

### Esqueleto de CSS recomendado

```css
@page { size: A4; margin: 2cm 2.2cm; }
body { font-family: "Hiragino Sans GB", "Heiti SC", "Noto Sans CJK SC", sans-serif;
       font-size: 11pt; color: #1a1a2e; line-height: 1.7; }
h1 { font-size: 22pt; text-align: center; }
h3 { font-size: 13pt; color: #1a73e8; }
table { width: 100%; border-collapse: collapse; font-size: 10pt; }
th { background: #1a73e8; color: #fff; padding: 7pt 10pt; text-align: left; }
td { padding: 6pt 10pt; border-bottom: 1px solid #e5e7eb; }
tr:nth-child(even) td { background: #f8f9fa; }
```

## Quando o reportlab É aceitável

Documentos somente em inglês, em que você precisa de layout programático preciso (gráficos, diagramas, posicionamento pixel-perfect). Use `platypus` (SimpleDocTemplate + Paragraph + Table), nunca a API `canvas` crua.

Referência: `tools/gen-73strings-pdfs.py`, bom exemplo de reportlab platypus para PDFs em inglês.

## Anti-padrões (de incidentes reais)

| Não faça | Por quê | Faça em vez disso |
|-------|-----|-----------|
| reportlab + STSong-Light para CJK | `•` → "煉", glifos incompletos | weasyprint + fontes do sistema |
| Posicionamento manual com `canvas` do reportlab | Coordenadas frágeis, texto desalinhado | weasyprint ou `platypus` do reportlab |
| CSS `font-family: -apple-system` | weasyprint não consegue resolver | Use `"Hiragino Sans GB"` |
| CSS `font-family: "PingFang SC"` | fontconfig costuma falhar em encontrar | Use `"Hiragino Sans GB"` |
| Helvetica-Bold em headers de tabela com CJK | Caracteres CJK viram ■■■ | Use fonte CJK + `font-weight: bold` |
| Hardcode de fonte sem checar | Falha em outro OS | Rode `fc-list :lang=zh` antes |

## Saída

Coloque o script gerado em `tools/gen-<name>-pdf.py`. O script deve:
1. Definir o HTML como uma constante string
2. Escrever HTML temporário → chamar weasyprint → remover o HTML temporário
3. Imprimir o caminho de saída em caso de sucesso
