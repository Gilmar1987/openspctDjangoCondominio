# controleCondominio

Cadastro de condomínios, seus apartamentos e (em breve) proprietários e moradores.

> **Atenção:** o MVP **não tem autenticação** (ADR-0005). Qualquer pessoa com acesso à aplicação lê e altera os dados de qualquer condomínio. Rode só localmente e não cadastre dados pessoais reais.

## Stack

Python 3.12 · Django 5.2 + Django REST Framework · Pydantic · PostgreSQL 17 · Pytest · Docker Compose (apenas desenvolvimento local).

As decisões de arquitetura ficam nas ADRs do store OpenSpec `tarefas` (`openspec/adrs/`).

## Subir o ambiente

```sh
cp .env.example .env        # ajuste DJANGO_SECRET_KEY e POSTGRES_PASSWORD
docker compose up -d --build
```

A aplicação fica em `http://localhost:8000/`. Se a porta 8000 já estiver em uso, defina outra em `WEB_PORT` no `.env`. As migrações rodam automaticamente na inicialização do serviço `web`.

Para parar: `docker compose down`. Para apagar também o banco local: `docker compose down -v`.

## Testes

```sh
docker compose run --rm web pytest
docker compose run --rm web pytest --cov --cov-config=.coveragerc   # exige 100% nos */domain.py
```

O GitHub Actions (`.github/workflows/ci.yml`) roda os mesmos testes em cada PR e push para `main`.

Não há testes E2E. Os cenários de interface são verificados com o roteiro em [docs/verificacao-navegador/](docs/verificacao-navegador/), e cada execução é registrada no próprio arquivo.

## Rotas

O condomínio (tenant) de cada operação vem do segmento `condominios/<id>/` da URL (ADR-0013).

| Operação | Página | API (JSON) |
|---|---|---|
| Listar / criar condomínios | `/condominios/`, `/condominios/novo/` | `GET` / `POST /api/condominios/` |
| Consultar condomínio | `/condominios/<id>/` (redireciona aos apartamentos) | `GET /api/condominios/<id>/` |
| Listar / criar apartamentos | `/condominios/<id>/apartamentos/`, `.../novo/` | `GET` / `POST /api/condominios/<id>/apartamentos/` |
| Consultar / editar apartamento | `.../apartamentos/<apt>/editar/` | `GET` / `PUT /api/condominios/<id>/apartamentos/<apt>/` |
| Excluir apartamento | `.../apartamentos/<apt>/excluir/` (pede confirmação) | `DELETE /api/condominios/<id>/apartamentos/<apt>/` |

Erros da API: `400 {"errors": {"<campo>": ["<mensagem em pt-BR>"]}}` e `404 {"detail": "Não encontrado."}`.

Exemplo:

```sh
curl -X POST http://localhost:8000/api/condominios/ -H "Content-Type: application/json" -d '{"name": "Residencial Aurora"}'
curl -X POST http://localhost:8000/api/condominios/<id>/apartamentos/ -H "Content-Type: application/json" \
     -d '{"tower": "A", "block": "1", "floor": 3, "number": "301"}'
```

## Estrutura

Vertical Slice com domínio rico (ADR-0001, ADR-0014): cada app (`condominiums`, `apartments`) tem `domain.py` (regras em Python puro), `inputs.py` (validação Pydantic), `repository.py` (ORM, sempre filtrado pelo tenant) e `features/<operação>.py` (handler + view da API + view HTML). `tenancy` é a plataforma de multi-tenant e `shared` concentra a tradução de erros e as respostas HTTP.
