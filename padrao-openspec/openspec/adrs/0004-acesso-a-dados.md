---
id: ADR-0004
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0004: Django ORM para acesso a dados

## Contexto

Com Django (ADR-0002) e PostgreSQL (ADR-0003), o projeto precisa de uma forma padrão de mapear entidades, executar consultas e versionar o esquema. O isolamento multi-tenant (ADR-0007) depende de filtrar `tenant_id` em todas as consultas.

## Decisão

- O acesso a dados SHALL usar o Django ORM, com migrações do Django.
- SQL bruto MUST ser justificado no design da change e MUST também filtrar por `tenant_id`.
- O acesso a dados de cada fatia SHALL ficar dentro da própria fatia (ADR-0001).

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| SQLAlchemy | Duplicaria o ORM nativo do Django e perderia migrações e admin integrados |
| Acesso direto (sem ORM) | Mais código manual e maior risco de esquecer o filtro de tenant |
| Prisma / Drizzle / EF Core / Dapper | Não pertencem ao ecossistema Python |

## Consequências

- Mais fácil: migrações automáticas, consultas expressivas, managers/querysets que podem aplicar o filtro de tenant por padrão.
- Mais difícil: separar entidades de domínio ricas (ADR-0001) dos models do ORM exige uma convenção explícita (models como entidades ou mapeamento entre eles).
- Risco aceito: consultas N+1 se `select_related`/`prefetch_related` não forem usados; pouco relevante no volume do MVP.
