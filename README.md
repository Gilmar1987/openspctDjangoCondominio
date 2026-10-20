# controleCondominio

Cadastro de condomínios, seus apartamentos, proprietários e moradores.

> **Atenção:** o MVP **não tem autenticação** (ADR-0005). Qualquer pessoa com acesso à aplicação lê e altera os dados de qualquer condomínio, inclusive os dados pessoais dos proprietários (nome, CPF, e-mail e telefone). Rode só localmente e **use apenas dados de teste**, nunca dados reais.

## Stack

Python 3.12 · Django 5.2 + Django REST Framework · Pydantic · PostgreSQL 17 · Pytest · Docker Compose (apenas desenvolvimento local).

As decisões de arquitetura ficam nas ADRs do store OpenSpec `tarefas` (`openspec/adrs/`).

## Subir o ambiente

```sh
cp .env.example .env        # ajuste DJANGO_SECRET_KEY, POSTGRES_PASSWORD e as duas chaves abaixo
docker compose up -d --build
```

### Chaves de proteção de dados (obrigatórias)

O CPF dos proprietários é guardado cifrado (ADR-0009). A aplicação não sobe sem estas variáveis no `.env`:

| Variável | Para que serve | Como gerar |
|---|---|---|
| `FIELD_ENCRYPTION_KEY` | Chave Fernet que cifra o CPF | `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| `CPF_HASH_KEY` | Segredo do hash HMAC usado na unicidade do CPF | `python -c "import secrets; print(secrets.token_hex(32))"` |

**Se a `FIELD_ENCRYPTION_KEY` for perdida ou trocada, os CPFs já gravados ficam ilegíveis.** Trocar a `CPF_HASH_KEY` quebra a verificação de CPF repetido nos cadastros existentes. Ainda não há rotação de chave. Para recomeçar do zero, apague o banco local com `docker compose down -v`.

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
| Excluir apartamento | `.../apartamentos/<apt>/excluir/` (pede confirmação; recusada se houver moradores) | `DELETE /api/condominios/<id>/apartamentos/<apt>/` (400 se houver moradores) |
| Listar / criar proprietários | `/condominios/<id>/proprietarios/`, `.../novo/` | `GET` / `POST /api/condominios/<id>/proprietarios/` |
| Consultar proprietário | `.../proprietarios/<prop>/` (CPF mascarado) | `GET /api/condominios/<id>/proprietarios/<prop>/` (único ponto com o CPF completo) |
| Editar proprietário | `.../proprietarios/<prop>/editar/` | `PUT /api/condominios/<id>/proprietarios/<prop>/` |
| Excluir proprietário | `.../proprietarios/<prop>/excluir/` (pede confirmação; desvincula os apartamentos) | `DELETE /api/condominios/<id>/proprietarios/<prop>/` |
| Listar / criar moradores | `/condominios/<id>/moradores/`, `.../novo/` (pode pré-preencher a partir de um proprietário) | `GET` / `POST /api/condominios/<id>/moradores/` |
| Consultar morador | `.../moradores/<mor>/` (CPF mascarado) | `GET /api/condominios/<id>/moradores/<mor>/` (único ponto com o CPF completo) |
| Editar morador (inclusive mudar de apartamento) | `.../moradores/<mor>/editar/` | `PUT /api/condominios/<id>/moradores/<mor>/` |
| Excluir morador | `.../moradores/<mor>/excluir/` (pede confirmação) | `DELETE /api/condominios/<id>/moradores/<mor>/` |

Um apartamento tem no máximo um proprietário (`owner_id`), e um proprietário pode ter N apartamentos (`apartment_ids`). O vínculo pode ser feito pelo apartamento ou pelo proprietário. Pelo proprietário, só são aceitos apartamentos livres ou que já são dele. Nas listagens, o CPF aparece mascarado (`***.982.247-**`).

**Moradores:**

- Um apartamento pode ter N moradores. Cada morador mora em **um único apartamento** do condomínio: o CPF é único entre os moradores dele, e mudar de apartamento é uma edição.
- Um apartamento com moradores não pode ser excluído. A API responde 400 em `{"errors": {"apartment": [...]}}`.
- Quando um morador e um proprietário do mesmo condomínio têm o mesmo CPF, o sistema reconhece que são a mesma pessoa (ADR-0017). As telas e a API mostram "também é proprietário (N apartamentos)" (`also_owner`) e "também é morador de …" (`resident_of`). Os cadastros continuam separados e **não se sincronizam**: corrigir um telefone num deles não altera o outro (ADR-0016).

Erros da API: `400 {"errors": {"<campo>": ["<mensagem em pt-BR>"]}}` e `404 {"detail": "Não encontrado."}`.

Exemplo:

```sh
curl -X POST http://localhost:8000/api/condominios/ -H "Content-Type: application/json" -d '{"name": "Residencial Aurora"}'
curl -X POST http://localhost:8000/api/condominios/<id>/apartamentos/ -H "Content-Type: application/json" \
     -d '{"tower": "A", "block": "1", "floor": 3, "number": "301"}'
curl -X POST http://localhost:8000/api/condominios/<id>/proprietarios/ -H "Content-Type: application/json" \
     -d '{"name": "Paulo", "cpf": "111.444.777-35", "apartment_ids": ["<apt1>", "<apt2>"]}'
curl -X POST http://localhost:8000/api/condominios/<id>/moradores/ -H "Content-Type: application/json" \
     -d '{"name": "Paulo", "cpf": "111.444.777-35", "apartment_id": "<apt1>"}'
```

## Estrutura

Vertical Slice com domínio rico (ADR-0001, ADR-0014): cada app (`condominiums`, `apartments`) tem `domain.py` (regras em Python puro), `inputs.py` (validação Pydantic), `repository.py` (ORM, sempre filtrado pelo tenant) e `features/<operação>.py` (handler + view da API + view HTML). `tenancy` é a plataforma de multi-tenant, e `shared` concentra a tradução de erros, as respostas HTTP, a criptografia e o filtro de dados pessoais nos logs. `people` é a base `Pessoa` (atributos gerais, validação e proteção do CPF) que `owners` (proprietário) e `residents` (morador) herdam (ADR-0016). Um app só importa de outro o `public.py` dele (ADR-0015), o que é conferido por `tests/test_architecture.py`.
