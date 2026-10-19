---
id: ADR-0002
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0002: Python + Django + Django REST Framework no back-end

## Contexto

O produto é um cadastro (CRUD com regras) de proprietários, apartamentos e moradores, com front-end renderizado no servidor, filas assíncronas e PostgreSQL. A stack precisa entregar persistência, migrações, páginas e API REST com pouco código de infraestrutura.

## Decisão

- O back-end SHALL ser escrito em Python com Django.
- Endpoints REST SHALL usar Django REST Framework.
- Dependências SHALL ser gerenciadas com pip + `requirements.txt`, com versões fixadas.
- Novas bibliotecas MUST ser justificadas no design da change que as introduzir.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Python + FastAPI | Não traz ORM, migrações, admin nem templates; exigiria montar essas peças |
| Python + Flask | Mesmo problema do FastAPI, com menos estrutura |
| TypeScript + Node.js | Não escolhido pelo dev |
| C# + .NET | Não escolhido pelo dev |
| Java/Kotlin (Spring Boot) | Não escolhido pelo dev |
| Go | Não escolhido pelo dev |
| uv / Poetry / pip-tools (dependências) | O dev escolheu pip + requirements.txt pela simplicidade |

## Consequências

- Mais fácil: CRUD, migrações, admin e templates vêm prontos; o ecossistema Django resolve multi-tenant, criptografia de campos e Celery com bibliotecas maduras.
- Mais difícil: Django incentiva "fat models" acoplados ao ORM, o que exige disciplina para manter o Domain Model rico (ADR-0001) separado da persistência.
- Risco aceito: pip + `requirements.txt` não gera lockfile com hashes por padrão; dependências transitivas podem variar entre instalações se não forem todas fixadas.
