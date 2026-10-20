# controleCondominio

Cadastro de condomínios, seus apartamentos e proprietários (e, em breve, moradores).

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
| Excluir apartamento | `.../apartamentos/<apt>/excluir/` (pede confirmação) | `DELETE /api/condominios/<id>/apartamentos/<apt>/` |
| Listar / criar proprietários | `/condominios/<id>/proprietarios/`, `.../novo/` | `GET` / `POST /api/condominios/<id>/proprietarios/` |
| Consultar proprietário | `.../proprietarios/<prop>/` (CPF mascarado) | `GET /api/condominios/<id>/proprietarios/<prop>/` (único ponto com o CPF completo) |
| Editar proprietário | `.../proprietarios/<prop>/editar/` | `PUT /api/condominios/<id>/proprietarios/<prop>/` |
| Excluir proprietário | `.../proprietarios/<prop>/excluir/` (pede confirmação; desvincula os apartamentos) | `DELETE /api/condominios/<id>/proprietarios/<prop>/` |

Um apartamento tem no máximo um proprietário (`owner_id`), e um proprietário pode ter N apartamentos (`apartment_ids`). O vínculo pode ser feito pelo apartamento ou pelo proprietário. Pelo proprietário, só são aceitos apartamentos livres ou que já são dele. Nas listagens, o CPF aparece mascarado (`***.982.247-**`).

Erros da API: `400 {"errors": {"<campo>": ["<mensagem em pt-BR>"]}}` e `404 {"detail": "Não encontrado."}`.

Exemplo:

```sh
curl -X POST http://localhost:8000/api/condominios/ -H "Content-Type: application/json" -d '{"name": "Residencial Aurora"}'
curl -X POST http://localhost:8000/api/condominios/<id>/apartamentos/ -H "Content-Type: application/json" \
     -d '{"tower": "A", "block": "1", "floor": 3, "number": "301"}'
curl -X POST http://localhost:8000/api/condominios/<id>/proprietarios/ -H "Content-Type: application/json" \
     -d '{"name": "Paulo", "cpf": "111.444.777-35", "apartment_ids": ["<apt1>", "<apt2>"]}'
```

## Estrutura

Vertical Slice com domínio rico (ADR-0001, ADR-0014): cada app (`condominiums`, `apartments`) tem `domain.py` (regras em Python puro), `inputs.py` (validação Pydantic), `repository.py` (ORM, sempre filtrado pelo tenant) e `features/<operação>.py` (handler + view da API + view HTML). `tenancy` é a plataforma de multi-tenant, e `shared` concentra a tradução de erros, as respostas HTTP, a criptografia e o filtro de dados pessoais nos logs. `people` é a base `Pessoa` (atributos gerais, validação e proteção do CPF) que `owners` herda e que as futuras entidades de pessoa também herdarão (ADR-0016). Um app só importa de outro o `public.py` dele (ADR-0015), o que é conferido por `tests/test_architecture.py`.
