---
id: ADR-0007
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0007: Multi-tenant com isolamento por coluna tenant_id

## Contexto

O produto atende vários condomínios (B2B2C), e os dados de um condomínio não podem vazar para outro. O volume é pequeno e há um único banco PostgreSQL (ADR-0003).

## Decisão

- Toda tabela de dados de negócio SHALL ter a coluna `tenant_id`, não nula.
- Toda consulta, escrita e relatório MUST filtrar por `tenant_id`; o filtro SHALL ser aplicado por padrão (ex.: manager/queryset base), não repetido à mão em cada fatia.
- Constraints de unicidade de negócio MUST incluir `tenant_id`.
- Testes de cada fatia MUST incluir um cenário que comprove que dados de outro tenant não são retornados nem alterados.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Schema por tenant | Migrações por schema e complexidade operacional desproporcionais ao MVP |
| Banco por tenant | Custo operacional alto para um ambiente local e volume pequeno |
| Single-tenant | O produto atende vários condomínios |

## Consequências

- Mais fácil: um único esquema e um único conjunto de migrações; relatórios entre tenants, se um dia necessários.
- Mais difícil: um filtro esquecido vaza dados entre condomínios; o risco é concentrado no código.
- Risco aceito: sem autenticação (ADR-0005), o `tenant_id` da requisição não tem origem confiável. A forma de resolver o tenant MUST ser definida na primeira change de cadastro.
