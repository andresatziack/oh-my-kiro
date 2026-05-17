# Agent Rules - Área de Staging

> Auto-destiladas a partir dos episodes. Injetadas pelo context-enrichment em cada mensagem.
> 🔴 = CRITICAL (sempre injetada) | 🟡 = RELEVANT (correspondência por palavra-chave)
> Seções criadas automaticamente por distill.sh. Máximo de 5 regras por seção.

## [memory,formation,hot-path,background]
🟡 1. Formacao de memoria tem dois timings: hot-path (em tempo real durante a conversa, efeito imediato mas aumenta latencia) serve para correcoes criticas; background (assincrono apos a conversa, sem impacto na resposta) serve para descoberta de padroes e destilacao de regras. Hoje auto-capture=hot-path, session-init=background, a combinacao faz sentido mas falta destilacao automatica na fase de background. Fonte: langchain-ai.github.io/langmem concepts
## [cc,macos,timeout,compatibility]
🔴 1. macOS nao tem o comando `timeout` (GNU coreutils). Plans escritos com `timeout 60s` no macOS dao command not found. Substitutos: `gtimeout` (brew install coreutils) ou `perl -e 'alarm(N); exec @ARGV'`. Nenhum script bash cross-platform pode supor que timeout exista
## [research,socratic,depth,compaction]
🔴 1. Ao pesquisar problemas complexos (otimizacao de long-running agent), pulou o auto-check socratico e jogou direto 6 direcoes de otimizacao. Causa raiz: depois da pesquisa, entrou em modo "martelo procurando prego", viu o paper dizer que X e problema e assumiu que o framework tambem tem X, sem verificar primeiro se a solucao atual ja cobria (o reinicio de iteration do Ralph Loop = compaction mais forte, foi confundido como "ausente"). Correcao no mecanismo: cada "sugestao/gap" que sai de uma pesquisa precisa passar pelas 3 camadas socraticas antes de entrar em findings: (1) esse problema realmente existe no framework atual (verificar a solucao existente); (2) e viavel na plataforma alvo (restricoes Kiro/CC); (3) o ganho > custo de manutencao. Gatilho: "saida de conclusao de pesquisa" ja e um ponto de decisao chave, nao apenas "escolha de design/solucao"
## [principle,reform,timid,optimization]
🟡 1. Na analise de solucoes de otimizacao, recuou para otimizacoes pequenas (3-9% de ganho) por achar "muitos efeitos colaterais" e "mudanca grande", evitando reforma a nivel de arquitetura (paralelismo multi-processo + isolamento por worktree). Correcao do usuario: a diretriz de topo "Bold reform over timid patches" exige resultado em primeiro lugar, sem medo de trabalhao. Efeito colateral nao e desculpa para evitar, e problema de engenharia para resolver. DO: defina primeiro o objetivo de melhor resultado e depois resolva os efeitos colaterais da implementacao. DON'T: rebaixar o objetivo e escolher solucao porca por causa dos efeitos colaterais
## [refactor,capability]
🟡 1. Refatoracao com foco excessivo em features novas quase perdeu a capacidade central do framework antigo

## [fs_write,kiro,tool,revert,modify]
🔴 1. A tool fs_write do Kiro restaura o arquivo modificado ao estado original entre duas tool calls. Toda modificacao de source code precisa ser feita em uma unica chamada execute_bash (script Python alterando em lote) e persistida com git commit na mesma chamada. Nao use fs_write para alterar source code esperando que o proximo tool call enxergue a mudanca
