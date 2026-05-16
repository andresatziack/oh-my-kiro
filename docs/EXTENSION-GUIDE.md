# Guia de Extensão do OMK

Referência rápida para estender o OMK em projetos downstream.

## Adicionar uma Skill

1. Crie `skills/my-skill/SKILL.md` com frontmatter e instruções
2. Registre em `.omk-overlay.json`:
   ```json
   { "extra_skills": ["skills/my-skill"], "extra_hooks": {} }
   ```
3. Valide: `bash tools/validate-project.sh`
4. Gere os configs: `python3 scripts/generate_configs.py --overlay .omk-overlay.json`

## Adicionar um Hook

1. Crie `hooks/project/my-hook.sh` (precisa ser executável)
2. Registre em `.omk-overlay.json`:
   ```json
   { "extra_hooks": { "postToolUse": [{"command": "hooks/project/my-hook.sh"}] } }
   ```
3. Eventos válidos (camelCase): `agentSpawn`, `userPromptSubmit`, `preToolUse`, `postToolUse`, `stop`
4. Valide: `bash tools/validate-project.sh`

## Instalar uma Skill da Comunidade

```bash
bash tools/install-skill.sh <SKILL_PATH>
```

Isso copia a skill, registra em `.omk-overlay.json` e regenera os configs.

## Validar seu projeto

```bash
bash tools/validate-project.sh [PROJECT_ROOT]
```

Sai com 1 em caso de erros (paths quebrados, JSON inválido, marcadores faltando).
Sai com 0 com warnings (frontmatter ausente, arquivos grandes).

## Sincronizar updates do OMK

```bash
bash tools/sync-omk.sh
```

Atualiza o submodule do OMK, valida e regenera todos os configs de agente.

## Don'ts

- **Não** edite arquivos dentro de `.omk/`, eles são regerados no sync
- **Não** duplique skills do framework, adicione apenas skills específicas do projeto
- **Não** dê o mesmo nome a hooks de projeto e a hooks do framework
- **Não** adicione regras de projeto ao `CLAUDE.md`, use as seções de projeto do `AGENTS.md`
- **Não** pule a validação, ela é um gate obrigatório antes da geração de configs
