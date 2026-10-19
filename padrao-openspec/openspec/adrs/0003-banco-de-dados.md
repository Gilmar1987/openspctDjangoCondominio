---
id: ADR-0003
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0003: PostgreSQL self-hosted em contêiner

## Contexto

Os dados são relacionais (proprietário ↔ apartamento ↔ morador), isolados por tenant e com dados pessoais. O projeto não tem ambiente de produção definido (ADR-0006) e roda localmente via docker-compose.

## Decisão

- A persistência SHALL usar PostgreSQL.
- O banco SHALL rodar self-hosted em contêiner Docker, definido no docker-compose do projeto.
- Alterações de esquema MUST ser feitas por migrações versionadas no repositório.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| MySQL / MariaDB | PostgreSQL tem melhor suporte no ecossistema Django e para constraints/índices por tenant |
| SQL Server | Licenciamento e menor alinhamento com Python/Django |
| SQLite | Inadequado para concorrência com worker Celery e para paridade de ambiente |
| MongoDB | Dados são relacionais; perderia o Django ORM |
| Banco gerenciado na cloud | O dev optou por self-hosted em contêiner |
| Self-hosted em VM | Sem ambiente de produção definido; contêiner basta para o desenvolvimento local |

## Consequências

- Mais fácil: ambiente local reproduzível; mesmo banco em todos os desenvolvedores; integridade referencial e constraints por `tenant_id`.
- Mais difícil: backup, atualização de versão e persistência do volume são responsabilidade do projeto.
- Risco aceito: a resposta original previa contêiner também em produção, mas não há produção definida; ao criar um ambiente de produção, a hospedagem do banco MUST ser revista em nova ADR.
