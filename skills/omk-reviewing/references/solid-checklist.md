# Prompts de Smell SOLID

## SRP (Single Responsibility)

- Arquivo dono de preocupações não relacionadas (por exemplo, HTTP + DB + regras de domínio em um único arquivo)
- Classe/módulo grande com baixa coesão ou múltiplos motivos para mudar
- Funções que orquestram muitos steps não relacionados
- God objects que sabem demais sobre o sistema
- **Pergunte**: "Qual é o único motivo pelo qual esse módulo mudaria?"

## OCP (Open/Closed)

- Adicionar um novo comportamento exige editar muitos blocos switch/if
- Crescimento de feature exige modificar a lógica central em vez de estender
- Sem pontos de plugin/strategy/hook para variação
- **Pergunte**: "Posso adicionar uma nova variante sem tocar no código existente?"

## LSP (Liskov Substitution)

- Subclasse checa o tipo concreto ou lança exceção em método da base
- Métodos sobrescritos enfraquecem precondições ou fortalecem postcondições
- Subclasse ignora ou no-op no comportamento do parent
- **Pergunte**: "Posso substituir qualquer subclasse sem que o caller perceba?"

## ISP (Interface Segregation)

- Interfaces com muitos métodos, a maioria não usada pelas implementadoras
- Callers dependem de interfaces amplas para necessidades estreitas
- Implementações vazias/stub de métodos da interface
- **Pergunte**: "Todas as implementadoras usam todos os métodos?"

## DIP (Dependency Inversion)

- Lógica de alto nível depende de tipos concretos de IO, storage ou network
- Implementações hardcoded em vez de abstrações ou injeção
- Cadeias de import que acoplam lógica de negócio à infraestrutura
- **Pergunte**: "Posso trocar a implementação sem alterar a lógica de negócio?"

---

## Code Smells comuns (além de SOLID)

| Smell | Sinais |
|-------|-------|
| **Long method** | Função > 30 linhas, múltiplos níveis de aninhamento |
| **Feature envy** | Método usa mais dados de outra classe do que da própria |
| **Data clumps** | Mesmo grupo de parâmetros passados juntos repetidamente |
| **Primitive obsession** | Usar strings/números em vez de tipos de domínio |
| **Shotgun surgery** | Uma alteração exige edits espalhados por muitos arquivos |
| **Divergent change** | Um arquivo muda por muitos motivos não relacionados |
| **Dead code** | Código inalcançável ou nunca chamado |
| **Speculative generality** | Abstrações para necessidades hipotéticas futuras |
| **Magic numbers/strings** | Valores hardcoded sem constantes nomeadas |

---

## Heurísticas de refactor

1. **Divida por responsabilidade, não por tamanho**, um arquivo pequeno ainda pode violar SRP
2. **Introduza abstração só quando necessário**, espere o segundo caso de uso
3. **Mantenha refactors incrementais**, isole o comportamento antes de mover
4. **Preserve o comportamento primeiro**, adicione testes antes de reestruturar
5. **Nomeie pelas intenções**, se é difícil nomear, a abstração pode estar errada
6. **Prefira composição sobre herança**, herança gera acoplamento forte
7. **Torne estados ilegais não representáveis**, use tipos para impor invariantes
