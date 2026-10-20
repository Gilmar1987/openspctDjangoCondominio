# Design

## Context

O repositório de código `C:\openspec\tarefas` só contém a configuração do OpenSpec e dos agentes (`.claude/`, `.agents/`, `.github/agents/`, `openspec/config.yaml`, `.gitignore`). Não há código, `requirements.txt`, Docker nem workflow de CI. A motivação está em proposal.md (Why), e o comportamento esperado está em `specs/condominios/spec.md` e `specs/apartamentos/spec.md`.

Restrições vigentes: ADR-0001 (Vertical Slice + domínio rico, REST entre fatias), ADR-0002 (Django + DRF, pip), ADR-0003 (PostgreSQL em contêiner, migrações versionadas), ADR-0004 (Django ORM), ADR-0005 (sem autenticação), ADR-0006 (docker-compose apenas local, `.env` + `.env.example`), ADR-0007 (`tenant_id` em toda tabela de negócio, filtro aplicado por padrão), ADR-0008 (templates Django, pt-BR, verificação em navegador versionada), ADR-0010 (monorepo), ADR-0012 (Pydantic). A ADR-0009 (LGPD) não se aplica porque esta change não trata dados pessoais. A ADR-0011 (Celery) fica para quando houver tarefa assíncrona.

## Architecture Decisions

Esta change toma duas decisões transversais, registradas como ADRs `Proposed`. Elas devem ser promovidas a `Accepted` antes do arquivamento:

- **ADR-0013 — `openspec/adrs/0013-resolucao-do-tenant-por-url.md`**: tenant vindo do segmento `condominios/<uuid>/`, `Condominium` e a resolução do tenant num pacote de plataforma `tenancy`, base `TenantOwnedModel` com `for_tenant()`. Complementa a ADR-0007 e esclarece o alcance da ADR-0001 (tenancy é plataforma, não fatia).
- **ADR-0014 — `openspec/adrs/0014-estrutura-de-uma-fatia.md`**: domínio puro em `domain.py`, ORM só em `models.py`/`repository.py`, validação só em Pydantic (`APIView` sem `Serializer`, views HTML sem `Form`), tradutor de erros pt-BR único. Cumpre o que as ADRs 0001 e 0012 pediram à primeira change.

Nenhuma ADR `Accepted` é contrariada.

## Goals / Non-Goals

**Goals:**
- Esqueleto executável com um comando (`docker compose up`) e testável com um comando (`pytest`), localmente e no CI.
- Fixar o padrão de fatia (ADR-0014) e de tenancy (ADR-0013) que as próximas changes vão copiar.
- 100% de cobertura de linhas e branches em `*/domain.py`, verificada no CI.

**Non-Goals:**
- Paginação da listagem (o volume do MVP é pequeno).
- Estilização além de um CSS mínimo próprio, sem framework de CSS.
- Imagem de produção, servidor WSGI de produção e coleta de estáticos para produção.
- Serviço Celery e broker no docker-compose.

## Decisions

### D1. Versões e dependências
Python 3.12, Django 5.2 (LTS), djangorestframework 3.16, pydantic 2.x, psycopg 3 (binary), pytest 8, pytest-django, pytest-cov. O `requirements.txt` fixa versões exatas (`==`) de todas as dependências diretas, com o patch mais recente disponível na implementação. Ficam em um arquivo só, porque não há ambiente de produção para separar.
*Alternativa:* Django 6.x. Ficou de fora porque a LTS 5.2 tem suporte até 2028 e é mais estável para a primeira base.

### D2. Layout do repositório
```
manage.py
config/            settings.py, urls.py, wsgi.py, asgi.py
tenancy/           models.py (Condominium, TenantOwnedModel, TenantQuerySet), public.py (resolve_tenant, get_condominium_or_404)
shared/            validation.py (tradução de erros Pydantic -> pt-BR), http.py (respostas de erro JSON), templates/base.html, static/css/app.css
condominiums/      domain.py, repository.py, inputs.py, features/{create,list,get}_condominium.py, urls.py, templates/
apartments/        domain.py, models.py, repository.py, inputs.py, features/{create,list,get,update,delete}_apartment.py, urls.py, templates/
tests/             espelha os pacotes: tests/condominiums/, tests/apartments/, tests/tenancy/, tests/shared/
docs/verificacao-navegador/cadastro-de-apartamentos.md
Dockerfile, docker-compose.yml, .env.example, requirements.txt, pytest.ini, .coveragerc, .github/workflows/ci.yml
```
O model `Condominium` fica em `tenancy` (ADR-0013). A fatia `condominiums` só tem as operações de cadastro e usa `tenancy.public`.

### D3. Identificadores
Chave primária UUID (v4) em `Condominium` e `Apartment`, gerada na aplicação. Inteiros sequenciais facilitariam enumerar recursos numa aplicação sem autenticação (ADR-0013).

### D4. Domínio
- `apartments/domain.py`: `Apartment` (dataclass imutável com `id`, `tenant_id`, `tower`, `block`, `floor`, `number`). A função `normalize_text` remove espaços nas extremidades e converte texto vazio em `None`. A propriedade `natural_key` devolve `(tower.casefold() or "", block.casefold() or "", number.casefold())`, base da unicidade. A exceção `DuplicateApartmentError` é usada pelos handlers.
- `condominiums/domain.py`: `CondominiumData` com a normalização do nome.
- Os limites de tamanho e de intervalo ficam nos modelos Pydantic (entrada), e as invariantes (normalização, chave natural) ficam no domínio. O domínio não importa Django nem Pydantic (ADR-0014).

### D5. Persistência e unicidade
- `TenantOwnedModel` (abstrato) declara `tenant = ForeignKey(Condominium, on_delete=PROTECT, db_column="tenant_id")`, índice em `tenant_id` e `objects = TenantQuerySet.as_manager()`, com `for_tenant(tenant_id)`. Os repositórios só consultam a partir de `for_tenant`.
- Os campos ausentes do apartamento são gravados como `NULL`.
- Unicidade no banco: `UniqueConstraint(F("tenant"), Lower(Coalesce("tower", Value(""))), Lower(Coalesce("block", Value(""))), Lower("number"), name="uniq_apartment_per_tenant")`. Isso cumpre a regra "ausentes iguais, sem diferenciar maiúsculas". `Lower` cobre o caso do pt-BR; o `casefold` do domínio é equivalente para os dados esperados.
- O handler verifica a duplicidade antes de gravar, para dar a mensagem amigável. Um `IntegrityError` dessa constraint (corrida) é convertido na mesma mensagem.
- Ordenação da listagem: `tower`, `block` e `floor` com `nulls_first=True`, depois `number`. Como o número é texto, a ordem é lexicográfica ("101" antes de "12"). Isso é aceito no MVP e coberto por teste.
*Alternativa:* `CITEXT`/collation case-insensitive. Ficou de fora porque exige extensão no PostgreSQL e a constraint por expressão já resolve.

### D6. Validação e erros (ADR-0014)
- `apartments/inputs.py`: `ApartmentInput` (Pydantic, `extra="ignore"`, `str_strip_whitespace=True`). `number` é texto de 1 a 10 caracteres; `tower` e `block` são texto opcional de até 20; `floor` é inteiro opcional de -5 a 200, com `strict` desligado para aceitar "3" vindo de formulário e rejeitar "terceiro". Texto vazio vira `None` antes da validação. O `extra="ignore"` faz um `tenant` enviado no corpo ser descartado (cenário "Tentativa de mudar o condomínio").
- `condominiums/inputs.py`: `CondominiumInput` com `name` de 1 a 120 caracteres após o strip.
- `shared/validation.py`: `to_ptbr_errors(ValidationError) -> dict[str, list[str]]`, que mapeia os tipos `missing`, `string_too_short`, `string_too_long`, `int_parsing`, `greater_than_equal` e `less_than_equal` para mensagens pt-BR com o nome do campo ("O número é obrigatório.", "O andar deve estar entre -5 e 200."). É o mesmo dicionário usado na API e nos templates.
- Formato da API: 400 com `{"errors": {"number": ["O número é obrigatório."]}}`. A duplicidade sai como `{"errors": {"apartment": ["Este apartamento já existe neste condomínio."]}}`, e o 404 como `{"detail": "Não encontrado."}`.

### D7. Tenancy por URL (ADR-0013)
`tenancy.public.get_condominium_or_404(condominium_id)` é chamado no início de toda view sob `condominios/<uuid:condominium_id>/`. O conversor `uuid` do Django já devolve 404 para um id malformado. Um apartamento de outro condomínio não é encontrado porque o repositório consulta `for_tenant(tenant_id).filter(id=...)`, e isso também resulta em 404 sem vazar existência.

### D8. Rotas
| Operação | Página (GET/POST) | API |
|---|---|---|
| Condomínios: listar / criar | `/condominios/`, `/condominios/novo/` | `GET/POST /api/condominios/` |
| Condomínio: consultar | `/condominios/<id>/` redireciona para os apartamentos | `GET /api/condominios/<id>/` |
| Apartamentos: listar / criar | `/condominios/<id>/apartamentos/`, `.../apartamentos/novo/` | `GET/POST /api/condominios/<id>/apartamentos/` |
| Apartamento: consultar / editar | `.../apartamentos/<apt>/editar/` | `GET/PUT /api/condominios/<id>/apartamentos/<apt>/` |
| Apartamento: excluir | `.../apartamentos/<apt>/excluir/` (GET confirma, POST exclui) | `DELETE /api/condominios/<id>/apartamentos/<apt>/` |

`/` redireciona para `/condominios/`. A edição na API é só `PUT` (substituição completa: o que for omitido fica ausente), sem `PATCH`. Os códigos HTTP seguem a spec (201/200/204/400/404).

### D9. API sem autenticação (ADR-0005)
DRF com `DEFAULT_AUTHENTICATION_CLASSES = []` e `DEFAULT_PERMISSION_CLASSES = ["rest_framework.permissions.AllowAny"]` explícitos, renderer só JSON (sem a API navegável, para não depender de templates do DRF). Sem `SessionAuthentication`, o DRF não exige CSRF na API. As páginas HTML mantêm `CsrfViewMiddleware`.

### D10. Ambiente local e configuração
- `Dockerfile` (`python:3.12-slim`, `pip install -r requirements.txt`) e `docker-compose.yml` com `db` (`postgres:17`, volume nomeado, healthcheck `pg_isready`) e `web` (`depends_on: db: condition: service_healthy`, comando `python manage.py migrate && python manage.py runserver 0.0.0.0:8000`, código montado como volume).
- As settings leem `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` e `POSTGRES_PORT` do ambiente (`os.environ`, sem dependência extra). Sem `DJANGO_SECRET_KEY`, a aplicação falha ao iniciar.
- `.env.example` versionado sem valores reais. O `.gitignore` passa a ignorar `.env`, `__pycache__/`, `.pytest_cache/`, `.coverage` e `htmlcov/`, preservando as regras atuais de `/openspec/*`.
- `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`, `USE_I18N = True` só para as mensagens nativas do Django, sem catálogos próprios.

### D11. Testes e CI
- `pytest.ini` com `DJANGO_SETTINGS_MODULE=config.settings`.
- Pirâmide: testes de domínio e de `shared/validation.py` puros, sem banco; testes de repositório e de feature (API com `APIClient`, páginas com o `client` do Django) com `@pytest.mark.django_db` no PostgreSQL. Cada requisito da spec tem ao menos um teste, e cada fatia tem teste de isolamento entre condomínios (ADR-0007).
- `.coveragerc` mede `*/domain.py` com `branch = True` e `fail_under = 100`. O CI roda `pytest --cov --cov-config=.coveragerc`.
- `.github/workflows/ci.yml`: em `pull_request` e `push` para `main`, `ubuntu-latest`, service container `postgres:17`, `actions/setup-python` 3.12 com cache de pip, `pip install -r requirements.txt` e `pytest`. As variáveis de teste ficam no próprio workflow, sem segredos.
- Sem E2E (decisão 5.5). Os cenários de interface são verificados em navegador seguindo o roteiro versionado em `docs/verificacao-navegador/cadastro-de-apartamentos.md`, com o resultado registrado no próprio arquivo.

## Risks / Trade-offs

- [Acesso irrestrito entre condomínios sem autenticação: superfície exposta da proposal] → Aplicação só local (ADR-0006); IDs UUID; `ALLOWED_HOSTS` restrito a `localhost,127.0.0.1` no `.env.example`; risco registrado na ADR-0013.
- [Novo esquema de dados: esquema e padrão de acesso da proposal] → Migrações iniciais versionadas; índice em `tenant_id`; constraint de unicidade no banco além da verificação no handler; teste que força a corrida do `IntegrityError`.
- [Nova configuração e segredos: variáveis de ambiente da proposal] → `.env.example` completo; falha explícita sem `DJANGO_SECRET_KEY`; `.env` no `.gitignore`; valores de teste declarados no workflow do CI.
- [Filtro de tenant esquecido em fatias futuras] → `for_tenant` como único caminho nos repositórios e teste de isolamento obrigatório por fatia. As próximas changes copiam o padrão.
- [Ordenação lexicográfica do número ("101" < "12")] → Aceita no MVP e documentada em teste; ordenação natural pode vir em change futura sem alterar a spec.
- [Pydantic sem integração nativa com DRF/Forms] → Tradutor único em `shared/validation.py` e testes que comparam a mensagem da API com a da página (cenário "Mesma validação nas duas interfaces").
- [Banco de testes no CI difere do local] → Mesma imagem `postgres:17` local e no CI.

**Raio de impacto**
- Arquivos-alvo (todos novos, exceto o `.gitignore`): `manage.py`, `config/*`, `tenancy/*`, `shared/*`, `condominiums/*`, `apartments/*`, `tests/*`, `docs/verificacao-navegador/cadastro-de-apartamentos.md`, `Dockerfile`, `docker-compose.yml`, `.env.example`, `requirements.txt`, `pytest.ini`, `.coveragerc`, `.github/workflows/ci.yml`, `.gitignore` (alterado).
- Dependentes afetados: nenhum código existente. O `.gitignore` alterado precisa continuar versionando `openspec/config.yaml` e ignorando o resto de `/openspec/`. `.github/agents/` e `.claude/` não são tocados.

## Migration Plan

Não há dados nem ambientes existentes. A primeira execução do `docker compose up` aplica as migrações iniciais. Rollback: `docker compose down -v` remove o banco local, e reverter o commit remove o código.

## Open Questions

- Ordenação natural do número do apartamento (ex.: "12" antes de "101"). Pode ser ajustada depois sem mudar specs nem tarefas desta change.
