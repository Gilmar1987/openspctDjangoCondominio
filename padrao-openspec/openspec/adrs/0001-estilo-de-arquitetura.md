---
id: ADR-0001
status: Accepted
date: 2026-10-19
supersedes:
superseded_by: ADR-0015 (somente a regra de comunicação entre módulos por REST/HTTP)
related_changes: []
---

# ADR-0001: Vertical Slice com Domain Model rico

## Contexto

O controleCondominio é um MVP pequeno (até 100 usuários ativos) que cadastra proprietários, apartamentos e moradores. A base de código precisa de uma organização que mantenha cada feature coesa e evolua por changes independentes, sem a cerimônia de várias camadas horizontais ou de serviços separados. As regras de negócio (vínculo proprietário–apartamento, moradores por unidade, isolamento por tenant) precisam de um lugar explícito.

## Decisão

- O back-end SHALL ser organizado em Vertical Slices: cada feature é uma fatia que reúne seu handler HTTP, validação de entrada, orquestração e acesso a dados.
- As regras de negócio SHALL viver em um Domain Model rico (DDD): entidades e value objects com comportamento. Handlers MUST NOT conter regra de negócio além da orquestração.
- A comunicação entre módulos SHALL usar contratos REST/HTTP. Uma fatia MUST NOT importar internals (models, handlers, serviços) de outra fatia.
- O sistema SHALL ser um único deploy (monólito Django).

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Monólito modular | Organização por capability com fronteiras mais largas; o dev preferiu fatias por feature |
| Clean Architecture | Camadas horizontais adicionam cerimônia desproporcional ao tamanho do MVP |
| Microsserviços | Custo operacional incompatível com um MVP de 100 usuários e sem deploy em produção |
| Serverless | Não combina com Django + Celery + PostgreSQL self-hosted |
| Serviços de domínio / CQRS / procedural (para as regras) | O dev escolheu entidades com comportamento (DDD) |

## Consequências

- Mais fácil: adicionar ou remover uma feature tocando uma única fatia; testar regras de domínio isoladas (exigência de 100% de cobertura no domínio).
- Mais difícil: o Django tende a centralizar `models.py` por app; será preciso definir onde as entidades de domínio ficam em relação aos models do ORM.
- Risco aceito: REST/HTTP entre módulos dentro do mesmo processo acrescenta latência e serialização onde uma chamada direta bastaria. Duplicação pontual de código entre fatias é aceita em troca de independência.
- A primeira change MUST definir a estrutura de pastas de uma fatia e o padrão de contrato REST entre módulos.
