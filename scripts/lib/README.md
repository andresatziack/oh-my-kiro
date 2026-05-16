# scripts/lib/ - Biblioteca compartilhada em Python

Usado por: `scripts/ralph_loop.py`, `scripts/generate_configs.py`
NÃO usado por: `hooks/**/*.sh` (hooks são em bash, sensíveis a latência)

## Regra de Fronteira

Hooks (bash, <5ms) ←→ protocolo via arquivo ←→ Scripts (Python, lógica complexa)

Nunca: hooks importando Python | scripts dando source em bash
