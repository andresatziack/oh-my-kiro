Fixer automático de PR: busca todos os comentários de review, faz triagem de cada um, aplica fix ou pushback, responde + resolve cada thread. Zero threads não resolvidas ao final.

## Step 1: Entender o PR

```bash
gh pr view <PR> --json number,title,body,headRefName,baseRefName,files,additions,deletions
gh pr diff <PR>
```

Leia o diff completo. Entenda o que o PR faz e por quê, esse contexto evita drift ao corrigir comentários individuais.

## Step 2: Buscar TODAS as threads de review não resolvidas

**Este step é OBRIGATÓRIO. NÃO pule.**

```bash
gh api graphql -f query='
query($owner:String!,$repo:String!,$pr:Int!) {
  repository(owner:$owner,name:$repo) {
    pullRequest(number:$pr) {
      reviewThreads(first:100) {
        nodes {
          id
          isResolved
          comments(first:5) {
            nodes { id body author { login } path line }
          }
        }
      }
    }
  }
}' -f owner='<OWNER>' -f repo='<REPO>' -F pr='<PR_NUMBER>'
```

Filtre para threads não resolvidas. Se zero não resolvidas → reporte "nothing to fix" e pare.

## Step 3: Triagem de cada thread

Para cada thread não resolvida, decida:

| Verdict | Significado | Ação |
|---------|---------|--------|
| **AGREE** | O reviewer está certo | Corrigir o código |
| **PUSHBACK** | O código atual é intencional ou o reviewer entendeu mal | Explicar por quê, sem alterar o código |

Mostre a tabela de triagem ao usuário antes de prosseguir:

```
| # | Thread ID | File:Line | Comment (summary) | Verdict | Reason |
```

## Step 4: Corrigir o código (apenas itens AGREE)

Para cada item AGREE:
1. Faça a alteração mínima de código
2. Verifique se o fix não quebra outras partes do PR

Após todos os fixes AGREE: rode build/lint/typecheck, se aplicável.

## Step 5: Responder + resolver CADA thread

**CRÍTICO: Tanto threads AGREE quanto PUSHBACK recebem uma resposta E são resolvidas. Sem exceções.**

### Para threads AGREE:
```bash
# Reply with what was fixed
gh api graphql -f query='mutation($tid:ID!,$body:String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId:$tid, body:$body}) {
    comment { id }
  }
}' -f tid='<THREAD_ID>' -f body='Fixed: <what changed>'

# Resolve
gh api graphql -f query='mutation($tid:ID!) {
  resolveReviewThread(input:{threadId:$tid}) { thread { isResolved } }
}' -f tid='<THREAD_ID>'
```

### Para threads PUSHBACK:
```bash
# Reply with explanation
gh api graphql -f query='mutation($tid:ID!,$body:String!) {
  addPullRequestReviewThreadReply(input: {pullRequestReviewThreadId:$tid, body:$body}) {
    comment { id }
  }
}' -f tid='<THREAD_ID>' -f body='Intentional: <explanation>. Happy to discuss.'

# Resolve (pushback is still a resolution)
gh api graphql -f query='mutation($tid:ID!) {
  resolveReviewThread(input:{threadId:$tid}) { thread { isResolved } }
}' -f tid='<THREAD_ID>'
```

## Step 6: Verificar zero não resolvidas + push

```bash
# Must be 0
gh api graphql ... --jq '[.nodes[] | select(.isResolved==false)] | length'
```

Commit, push, reporte:

```
## @fixpr Summary
- AGREE (fixed): N
- PUSHBACK (replied): M
- All threads resolved: ✅
```

---
User's task:
(O usuário fornece a URL/número do PR. Se não houver, detecte a partir da branch atual.)
