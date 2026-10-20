---
id: ADR-0013
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: [cadastro-de-apartamentos]
---

# ADR-0013: Resolução do tenant pelo segmento de URL e tenancy como plataforma

## Contexto

A ADR-0007 isola os dados por `tenant_id` e exige que a primeira change defina como a requisição informa o tenant. Sem autenticação (ADR-0005), não existe sessão de usuário da qual derivar o condomínio. Já a ADR-0001 proíbe uma fatia de importar internals de outra e manda que os módulos conversem por REST/HTTP. Toda fatia de negócio, porém, precisa validar o condomínio da requisição e referenciá-lo por chave estrangeira. Fazer uma chamada HTTP in-process só para isso seria custo sem benefício.

## Decisão

- O condomínio (tenant) da requisição SHALL vir do segmento de caminho `condominios/<id>/`: páginas em `/condominios/<id>/...` e API em `/api/condominios/<id>/...`.
- O identificador do condomínio SHALL ser um UUID gerado pelo sistema.
- A entidade `Condominium` (a tabela de tenants) e a resolução do tenant SHALL ficar em um pacote de plataforma `tenancy`. Esse pacote é infraestrutura transversal, como as settings, e não uma fatia de negócio. Toda fatia MAY importar a API pública de `tenancy` (`tenancy/public.py`). A regra de REST entre módulos da ADR-0001 continua valendo entre fatias de negócio.
- Toda view de dados de negócio MUST resolver o tenant pela API pública de `tenancy`, que responde 404 quando o condomínio não existe, antes de qualquer leitura ou escrita.
- Todo model de dados de negócio MUST herdar a base `TenantOwnedModel` (FK `tenant`, coluna `tenant_id`), e toda consulta MUST partir de `Model.objects.for_tenant(tenant_id)`.
- Quando a autenticação for adotada, a ADR que substituir a ADR-0005 MUST rever esta decisão. O tenant deverá ser validado contra o usuário autenticado.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Cabeçalho `X-Tenant-ID` + sessão na interface | Dois mecanismos diferentes para a mesma regra; menos visível e menos testável |
| Tenant fixo por variável de ambiente | Não exercita o multi-tenant da ADR-0007 |
| Subdomínio por condomínio | Exige DNS/hosts locais; desproporcional para o ambiente local |
| Condomínio dentro da fatia `condominiums` e acessado por REST | Chamada HTTP in-process em toda requisição, sem ganho de isolamento |
| IDs inteiros sequenciais | Facilitam enumerar condomínios numa aplicação sem autenticação |

## Consequências

- Mais fácil: o tenant fica explícito em cada URL e em cada teste; trocar o mecanismo depois afeta só `tenancy` e o roteamento.
- Mais difícil: toda rota de negócio carrega o segmento do condomínio.
- Risco aceito: sem autenticação, qualquer pessoa troca o UUID na URL e acessa outro condomínio. O UUID só dificulta a enumeração, não protege. O risco é aceito porque a aplicação só roda localmente (ADR-0006).
