# Upgrade de Capacidade de Debugging - Inteligência Diagnóstica Dirigida por LSP

**Objetivo:** Reescrever a debugging skill, embutindo a toolchain de LSP e um mecanismo de evidencia diagnostica; usar lembretes automaticos via hook e regras obrigatorias para evoluir o debugging do agent de "grep + chute" para "analise semantica + evidencia".
**Não-Objetivos:** Nao criar novo subagent; nao introduzir ferramenta externa (apenas as ferramentas LSP/code ja disponiveis); nao alterar ralph_loop.py.
**Arquitetura:** Tres camadas de garantia: skill ensina o metodo + rule obriga a escolha de ferramenta + hook lembra automaticamente. Modificar 5 arquivos, criar 0. Hook nao consegue observar a chamada de ferramenta do agent, entao nao ha closed loop de verificacao; a coercao vem da camada de rule (agent internaliza a regra).
**Tech Stack:** Bash (hooks), Markdown (skill/rules)

## Tarefas

### Tarefa 1: reescrever a debugging skill - embutir a toolchain LSP

**Arquivos:**
- Modify: `skills/debugging/SKILL.md`
- Modify: `skills/debugging/reference.md`
- Test: `tests/test_debugging_skill.py`

**Step 1: Write failing test**

```python
# tests/test_debugging_skill.py
import pytest
from pathlib import Path

SKILL = Path("skills/debugging/SKILL.md").read_text()
REF = Path("skills/debugging/reference.md").read_text()

class TestDebuggingSkillContent:
    def test_has_tool_decision_matrix(self):
        assert "## Tool Decision Matrix" in SKILL

    def test_has_lsp_tools_in_phase1(self):
        p1_start = SKILL.index("### Phase 1")
        p2_start = SKILL.index("### Phase 2")
        p1 = SKILL[p1_start:p2_start]
        for tool in ["get_diagnostics", "search_symbols", "find_references"]:
            assert tool in p1, f"Phase 1 missing {tool}"

    def test_has_diagnostic_evidence_requirement(self):
        assert "Diagnostic Evidence" in SKILL

    def test_has_pre_post_diagnostics(self):
        assert SKILL.count("get_diagnostics") >= 3

    def test_has_episodes_check(self):
        p1_start = SKILL.index("### Phase 1")
        p2_start = SKILL.index("### Phase 2")
        assert "episodes" in SKILL[p1_start:p2_start].lower()

    def test_has_iron_laws(self):
        s = SKILL.lower()
        assert "goto_definition" in s
        assert "find_references" in s
        assert "get_diagnostics" in s

    def test_preserves_existing_content(self):
        for section in ["Red Flags", "Common Rationalizations", "Quick Reference"]:
            assert section in SKILL, f"Lost existing section: {section}"

    def test_preserves_four_phases(self):
        for phase in ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]:
            assert phase in SKILL, f"Lost {phase}"

    def test_reference_has_tool_recipes(self):
        for t in ["search_symbols", "goto_definition", "find_references", "get_hover", "get_diagnostics"]:
            assert t in REF, f"Reference missing {t}"
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debugging_skill.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Rewrite `skills/debugging/SKILL.md`:
- PRESERVE existing valuable content: Red Flags section, Common Rationalizations table, Quick Reference table, Phase 2-4 detailed steps
- Add Tool Decision Matrix (bug type → tool sequence) — new section before Phase 1
- AUGMENT Phase 1 with LSP tool steps (get_diagnostics → search_symbols → find_references → get_hover → Diagnostic Evidence) — add to existing Phase 1, don't replace
- Add Three Iron Laws (no goto_definition = no modify; no find_references = no refactor; no get_diagnostics = no claim fixed)
- Add episodes.md check as Phase 1 Step 0
- Add pre/post get_diagnostics comparison in Phase 4

Rewrite `skills/debugging/reference.md`:
- Add concrete tool recipes for each LSP tool
- Keep existing multi-component diagnostic patterns

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debugging_skill.py -v`
Expected: PASS

**Step 5: Commit**

### Tarefa 2: atualizar regras de debugging - LSP-first como regra dura

**Arquivos:**
- Modify: `.claude/rules/debugging.md`
- Modify: `.kiro/rules/code-analysis.md`
- Test: `tests/test_debugging_rules.py`

**Step 1: Write failing test**

```python
# tests/test_debugging_rules.py
import pytest
from pathlib import Path

class TestDebuggingRules:
    def test_claude_rules_has_lsp(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "get_diagnostics" in r
        assert "goto_definition" in r or "search_symbols" in r

    def test_claude_rules_has_evidence(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "evidence" in r.lower() or "证据" in r

    def test_claude_rules_has_lsp_priority(self):
        r = Path(".claude/rules/debugging.md").read_text()
        assert "LSP" in r or "lsp" in r

    def test_kiro_code_analysis_covers_debugging(self):
        r = Path(".kiro/rules/code-analysis.md").read_text()
        assert "调试" in r or "debug" in r.lower()
        assert "get_diagnostics" in r
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debugging_rules.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Upgrade `.claude/rules/debugging.md` — add rules 4-7:
4. Para debugar problema de codigo, primeiro use as ferramentas LSP (get_diagnostics, search_symbols, find_references, goto_definition, get_hover) para fazer analise semantica. grep so para comentarios, strings ou configuracao.
5. Antes de corrigir um bug, e obrigatorio produzir Diagnostic Evidence: quais ferramentas LSP foram usadas, o que foi encontrado e qual a causa raiz. Sem evidencia, sem fix.
6. Apos a correcao, get_diagnostics e obrigatorio para validar; so se conta concluido se as novas diagnostics estiverem em 0.
7. Codigo desconhecido: primeiro goto_definition para entender a implementacao -> find_references para entender o uso -> so depois alterar.

Upgrade `.kiro/rules/code-analysis.md` - acrescentar paragrafo de debugging deixando claro que get_diagnostics e a primeira ferramenta a ser usada.

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debugging_rules.py -v`
Expected: PASS

**Step 5: Commit**

### Tarefa 3: gatilho de hook - context-enrichment detecta cenario de debugging

**Arquivos:**
- Modify: `hooks/feedback/context-enrichment.sh`
- Test: `tests/test_debug_hook_trigger.py`

**Step 1: Write failing test**

```python
# tests/test_debug_hook_trigger.py
import subprocess, json, pytest

HOOK = "hooks/feedback/context-enrichment.sh"

def run_hook(prompt):
    r = subprocess.run(["bash", HOOK], input=json.dumps({"prompt": prompt}),
                       capture_output=True, text=True, timeout=10)
    return r.stdout

class TestDebugHookTrigger:
    def test_chinese_error(self):
        assert "🐛" in run_hook("测试报错了，帮我看看")

    def test_english_error(self):
        assert "🐛" in run_hook("tests are failing, looks like something broke")

    def test_bug_keyword(self):
        assert "🐛" in run_hook("这个 bug 怎么修")

    def test_traceback(self):
        assert "🐛" in run_hook("got a traceback in the logs")

    def test_broken_keyword(self):
        assert "🐛" in run_hook("build is broken after the last commit")

    def test_bug_english(self):
        assert "🐛" in run_hook("there's a bug in the parser")

    def test_no_false_positive_chinese(self):
        out = run_hook("帮我写个新功能")
        assert "🐛" not in out

    def test_no_false_positive_error_handling(self):
        out = run_hook("add error handling to the parser")
        assert "🐛" not in out

    def test_no_false_positive_debug_logging(self):
        out = run_hook("add debug logging to the service")
        assert "🐛" not in out
```

**Step 2: Run test — verify it fails**
Run: `python3 -m pytest tests/test_debug_hook_trigger.py -v`
Expected: FAIL

**Step 3: Write minimal implementation**
Apos o Research reminder de context-enrichment.sh, adicionar:
```bash
# Debugging skill reminder + flag
if echo "$USER_MSG" | grep -qE '(报错|bug|调试|修复.*错误|测试失败|不工作了)'; then
  echo "🐛 Debug detected → read skills/debugging/SKILL.md. Use LSP tools (get_diagnostics, search_symbols, find_references) BEFORE attempting fixes."
elif echo "$USER_MSG" | grep -qiE '(\btest.*(fail|brok)|traceback|exception.*thrown|crash|not working|fix.*bug|\bis broken\b|\bbug\b)'; then
  echo "🐛 Debug detected → read skills/debugging/SKILL.md. Use LSP tools (get_diagnostics, search_symbols, find_references) BEFORE attempting fixes."
fi
```

**Step 4: Run test — verify it passes**
Run: `python3 -m pytest tests/test_debug_hook_trigger.py -v`
Expected: PASS

**Step 5: Commit**


## Checklist

- [x] debugging skill contem Tool Decision Matrix | `grep -q 'Tool Decision Matrix' skills/debugging/SKILL.md`
- [x] Phase 1 da debugging skill referencia ferramentas LSP | `python3 -c "t=open('skills/debugging/SKILL.md').read(); p1=t[t.index('### Phase 1'):t.index('### Phase 2')]; assert all(x in p1 for x in ['get_diagnostics','search_symbols','find_references'])"`
- [x] debugging skill exige Diagnostic Evidence | `grep -q 'Diagnostic Evidence' skills/debugging/SKILL.md`
- [x] debugging skill traz as tres iron laws | `grep -q 'goto_definition' skills/debugging/SKILL.md && grep -q 'find_references' skills/debugging/SKILL.md`
- [x] reference.md tem recipes das ferramentas | `python3 -c "t=open('skills/debugging/reference.md').read(); assert all(x in t for x in ['search_symbols','goto_definition','find_references','get_hover','get_diagnostics'])"`
- [x] regras de debugging exigem LSP | `grep -q 'get_diagnostics' .claude/rules/debugging.md && grep -qE '(LSP|lsp)' .claude/rules/debugging.md`
- [x] kiro code-analysis cobre debugging | `grep -qE '(调试|debug)' .kiro/rules/code-analysis.md && grep -q 'get_diagnostics' .kiro/rules/code-analysis.md`
- [x] context-enrichment detecta debugging em chines | `echo '{"prompt":"测试报错了"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] context-enrichment detecta debugging em ingles | `echo '{"prompt":"tests are failing"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] context-enrichment sem disparo equivocado | `! echo '{"prompt":"帮我写个新功能"}' | bash hooks/feedback/context-enrichment.sh 2>/dev/null | grep -q '🐛'`
- [x] todos os testes passam | `python3 -m pytest tests/test_debugging_skill.py tests/test_debugging_rules.py tests/test_debug_hook_trigger.py -v`

## Review

### Round 1 (4 reviewers)

- **Goal Alignment:** REQUEST CHANGES - a Tarefa 4 oferece apenas warning suave, nao bloqueio forte; isso destoa do objetivo "mecanismo obrigatorio de evidencia diagnostica" e "verification closed loop". Sugestao: ou promover para bloqueio forte ou ajustar o texto do objetivo. Tarefas 1-3 estao alinhadas, sem dependencia ruim de ordem; non-goals respeitados.
- **Verify Correctness:** REQUEST CHANGES - 3 problemas: (1) o item da checklist "sem trigger equivocado" usa `grep -qv '🐛'`; com saida de varias linhas isso passa sempre (false positive); deve mudar para `! grep -q '🐛'`; (2) o item "stop hook checa uso de LSP" referencia `tests/verify_debug_stop_hook.sh`, que nao existe e nao esta na lista de arquivos do plan; (3) verify-completion.sh tem caminhos de early exit (stop_hook_active=true ou itens unchecked); o trecho de validacao de debug da Tarefa 4 pode nunca ser executado.
- **Completeness:** REQUEST CHANGES - 3 problemas: (1) o SKILL.md atual tem 200+ linhas de conteudo rico (Red Flags, Common Rationalizations, Quick Reference etc.); o teste so checa keywords e o rewrite pode descartar conteudo valioso; (2) "investigate" aparece em ambos os greps de research e debug, gerando duplo trigger; (3) os 4 arquivos de teste nao estao registrados no CI.
- **Technical Feasibility:** REQUEST CHANGES - 2 blockers: (1) verify-log nao tem produtor; nenhum componente registra uso de LSP no verify-log, entao a checagem da Tarefa 4 sempre alerta (defeito arquitetural); (2) grep com 'error'/'fail' tem altissima taxa de falso positivo ("error handling", "fail-safe" etc. caem nele). Alem disso, o flag file e por workspace hash em vez de session, sobrescrevendo entre debugs.

### Round 2 fixes applied

| Issue | Fix |
|-------|-----|
| Tarefa 4 sem produtor de verify-log (arquitetura inviavel) | Remover Tarefa 4. Reduzir o objetivo de "verification closed loop" para "lembrete automatico via hook + obrigacao via rule". Hook nao observa chamadas de ferramenta; coercao vem da camada de rule |
| grep 'error'/'fail' com falso positivo | Apertar a pattern em ingles para `test.*(fail\|brok)\|traceback\|exception.*thrown\|crash\|not working\|fix.*bug\|is broken\|\\bbug\\b`, excluindo discussoes legitimas como "error handling" e "debug logging" |
| `grep -qv` com falso positivo | Trocar para `! grep -q` |
| `tests/verify_debug_stop_hook.sh` inexistente | Remover esse item da checklist (Tarefa 4 ja foi removida) |
| Reescrever SKILL.md pode perder conteudo | Adicionar diretiva PRESERVE + teste de retencao de conteudo (Red Flags, Common Rationalizations, Quick Reference, 4 Phases) |
| "investigate" sobrepoe deteccao de research | A pattern apertada em ingles ja exclui investigate |
| Flag file deixa de ser util (Tarefa 4 removida) | Remover a escrita do flag file |

### Round 2 re-review (2 reviewers)

- **Fixes verification:** APPROVE — all 7 fixes correctly address Round 1 issues. No new problems introduced.
- **Technical Feasibility (grep patterns):** REQUEST CHANGES — `broke` doesn't match `broken`, `bug` removed from English pattern. **Fixed:** `broke` → `brok` (matches broke/broken), added `\bis broken\b` and `\bbug\b`. Trade-off accepted: `getting an error` still missed but adding `error` would reintroduce false positives.

**Final verdict: APPROVE (Round 2 pattern fix applied, all angles satisfied)**

## Errors

| Error | Task | Attempt | Resolution |
|-------|------|---------|------------|

## Descobertas

