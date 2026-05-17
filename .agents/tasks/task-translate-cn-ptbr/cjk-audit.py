"""Audit which files have narrative-prose CJK vs only in-fence / inline-code CJK.

Reads /tmp/cjk-current.txt (one path per line). Prints two groups:
  1) files with CJK in narrative prose (require translation)
  2) files with CJK only inside fenced code blocks or inline backtick spans
"""
import re

files = []
for line in open('/tmp/cjk-current.txt'):
    p = line.strip()
    if p.startswith('./'):
        p = p[2:]
    if p:
        files.append(p)

cjk_re = re.compile(r'[\u4e00-\u9fff]')
results = {}
for f in files:
    in_fence = False
    in_lines, out_lines = [], []
    with open(f, 'r') as fh:
        for i, line in enumerate(fh, 1):
            stripped = line.strip()
            if re.match(r'^(```|~~~)', stripped):
                in_fence = not in_fence
                continue
            if not cjk_re.search(line):
                continue
            if in_fence:
                in_lines.append(i)
                continue
            stripped_inline = re.sub(r'`[^`]*`', '', line)
            if cjk_re.search(stripped_inline):
                out_lines.append((i, line.rstrip()))
            else:
                in_lines.append(i)
    results[f] = (len(in_lines), out_lines)

prose_files = [(f, ol) for f, (_il, ol) in results.items() if ol]
in_only_files = [(f, ic) for f, (ic, ol) in results.items() if not ol]
print(f"Files with NARRATIVE-PROSE CJK (need translation in FEAT-007): {len(prose_files)}")
for f, lines in prose_files:
    print(f"  {f} ({len(lines)} prose lines)")
    for ln, content in lines[:3]:
        print(f"    {ln}: {content[:140]}")
print()
print(f"Files with ONLY in-fence/inline-code CJK (legitimate per rules): {len(in_only_files)}")
for f, n in in_only_files:
    print(f"  {f} ({n} in-fence/inline lines)")
