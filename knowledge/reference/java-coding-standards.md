# Padrões de Código Java

> Regras prescritivas para o Agent escrever código Java. Carregadas ao tocar em arquivos Java.
> Companheiro de `java-architect.md` (referência de stack Spring Boot).

## Effective Java

- Prefira métodos factory estáticos a construtores públicos
- Use o padrão Builder quando o construtor tiver mais de 3 parâmetros
- Use `record` para portadores puros de dados (DTOs, value objects) - Java 16+
- Prefira imutabilidade: deixe os campos `final` e não forneça setters
- Prefira composição em vez de herança
- Prefira interfaces a classes abstratas
- Use `sealed class` para restringir a hierarquia de herança - Java 17+
- Nunca use raw types, sempre parametrize generics
- Retorne coleções vazias em vez de null
- Use `Optional` para retornos que podem estar ausentes, nunca para campos ou parâmetros
- Use enums em vez de constantes int/String
- Minimize a mutabilidade, menos partes em movimento, menos bugs

## Clean Code

- Faça uma coisa por método, Single Responsibility Principle
- Mantenha métodos curtos, normalmente abaixo de 20 linhas, divida quando ficar maior
- Use nomes auto-documentados: substantivos para classes, verbos para métodos, `is/has/can` para booleanos
- Nunca use parâmetros booleanos como flag, divida em dois métodos
- Nunca engula exceções: o catch precisa logar ou relançar
- Nunca capture `Exception` ou `Throwable`, use tipos de exceção específicos
- Inclua o objeto de exceção no log: `log.error("message", e)` e não `log.error("message")`
- Nada de `System.out.println`, use logger SLF4J
- Use comentários para explicar POR QUE, não O QUE; o código deve se auto-explicar
- Sem abstração prematura (YAGNI), resolva o problema atual e abstraia quando precisar

## Clean Architecture

- Direção de dependência: camadas externas para camadas internas, nunca o contrário
- Sem lógica de negócio em Controller ou Interceptor, delegue para o Service
- Dependa de interfaces, não de implementações concretas, na camada de Service
- Prefira injeção via construtor a `@Autowired` em campo
- Não vaze DTO/VO para a camada de domínio

## Sistemas Distribuídos

- Nunca misture chamadas de API externa com operações de DB local na mesma `@Transactional`
- Faça operações reversíveis primeiro e operações irreversíveis por último
- Considere idempotência em todas as operações de escrita
- Não dependa de cache em memória de uma única máquina para consistência em sistemas multi-node
- Tenha estratégia de timeout e retry para chamadas entre serviços

## Testing

- Matchers do Mockito devem ser consistentes: ou todos matchers ou todos valores concretos, nunca misture
- Não faça mock de value objects (records, DTOs), construa-os diretamente
- Use a convenção de nomenclatura: `methodName_condition_expectedResult`
- Cada teste verifica exatamente um comportamento
- Prefira argumentos específicos em `verify()`, evite `any()` salvo quando realmente necessário

## Workflow do Agent

- Antes de modificar uma interface: faça find-references para listar todas as implementações e callers
- Após modificar uma interface: rode imediatamente `mvn compile -pl <module> -am`
- Após todas as mudanças: rode `mvn clean test`, não confie em compilação incremental
- Antes de refatoração complexa (≥3 arquivos): escreva um plan e aguarde a confirmação do usuário
- Antes de fazer commit: rode `git diff --stat` para confirmar que o escopo da mudança bate com a intenção
- Antes de criar uma nova classe/interface: pesquise se uma abstração similar já existe
