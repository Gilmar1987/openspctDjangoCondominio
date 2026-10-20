# Tasks

Repositório de código: `C:\openspec\tarefas`. Os caminhos abaixo são relativos a ele, exceto quando indicado.

## 1. Fundação do projeto

- [x] 1.1 Criar `requirements.txt` com as versões exatas (`==`) de Django 5.2.x, djangorestframework 3.16.x, pydantic 2.x, psycopg[binary] 3.x, pytest 8.x, pytest-django e pytest-cov (D1). Verificar que `pip install -r requirements.txt` termina sem erro num venv Python 3.12.
- [x] 1.2 Criar `manage.py` e `config/{__init__,settings,urls,wsgi,asgi}.py`, com as settings lendo as variáveis de ambiente de D10 e falhando sem `DJANGO_SECRET_KEY`; DRF configurado conforme D9; `LANGUAGE_CODE="pt-br"`, `TIME_ZONE="America/Sao_Paulo"`. Verificar com `python manage.py check` sem erros, com as variáveis definidas.
- [x] 1.3 Criar `Dockerfile`, `docker-compose.yml` (serviços `db` com `postgres:17` + healthcheck e `web`) e `.env.example`, sem valores reais e com `DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1` (D10; mitigação do risco de configuração/segredos). Verificar com `docker compose up -d` e `docker compose ps`, que deve mostrar `db` healthy e `web` respondendo em `http://localhost:8000/`.
- [x] 1.4 Atualizar `.gitignore` com `.env`, `__pycache__/`, `.pytest_cache/`, `.coverage` e `htmlcov/`, mantendo `/openspec/*` e `!/openspec/config.yaml`. Verificar com `git check-ignore .env` (ignorado) e `git ls-files openspec/config.yaml` (continua versionado).
- [x] 1.5 Criar `pytest.ini` (`DJANGO_SETTINGS_MODULE=config.settings`) e `.coveragerc` (`source` nos `*/domain.py`, `branch = True`, `fail_under = 100`), mais um teste de fumaça `tests/test_smoke.py` que confirma que `/` redireciona para `/condominios/`. Verificar com `docker compose run --rm web pytest`, que deve coletar e passar o teste.
- [x] 1.6 Criar `.github/workflows/ci.yml` (D11): gatilhos `pull_request` e `push` em `main`, service `postgres:17`, Python 3.12 com cache de pip, `pip install -r requirements.txt`, `pytest --cov --cov-config=.coveragerc` e variáveis de teste no próprio arquivo. Verificar que o YAML é válido (`python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/ci.yml'))"`) e, depois do push da branch, que o job roda verde no PR.

## 2. Plataforma compartilhada: tenancy e validação

- [x] 2.1 Escrever os testes `tests/shared/test_validation.py` (cada tipo de erro Pydantic de D6 vira a mensagem pt-BR esperada, com o nome do campo) e `tests/tenancy/test_public.py` (`get_condominium_or_404` devolve o condomínio existente e levanta 404 para UUID inexistente; `for_tenant` só devolve linhas do tenant pedido). Verificar que os testes falham por ausência de implementação.
- [x] 2.2 Implementar `shared/validation.py` (`to_ptbr_errors`) e `shared/http.py` (respostas JSON `{"errors": ...}` e `{"detail": "Não encontrado."}`). Verificar com `pytest tests/shared` passando.
- [x] 2.3 Implementar `tenancy/models.py` (`Condominium` com PK UUID e `name`; `TenantQuerySet.for_tenant`; `TenantOwnedModel` abstrato com FK `tenant`/`db_column="tenant_id"` e índice), `tenancy/public.py` e a migração inicial `tenancy/migrations/0001_initial.py` (D3, D5, D7, ADR-0013). Verificar com `pytest tests/tenancy` passando e `python manage.py makemigrations --check` sem pendências.
- [x] 2.4 Criar `shared/templates/base.html` (layout pt-BR, bloco de mensagens) e `shared/static/css/app.css` mínimo. Verificar abrindo `/condominios/` no navegador depois do grupo 3: a página herda o layout.

## 3. Capability `condominios`

- [x] 3.1 Escrever `tests/condominiums/test_domain.py` (normalização do nome) e `tests/condominiums/test_inputs.py` (nome obrigatório, em branco, 120 e 121 caracteres). Verificar que os testes falham antes da implementação.
- [x] 3.2 Implementar `condominiums/domain.py` e `condominiums/inputs.py` (D4, D6). Verificar com `pytest tests/condominiums/test_domain.py tests/condominiums/test_inputs.py` passando e 100% de cobertura em `condominiums/domain.py`.
- [x] 3.3 Escrever `tests/condominiums/test_api.py` e `tests/condominiums/test_pages.py`, cobrindo os cenários de `specs/condominios/spec.md`: criação válida (201 + UUID), nome vazio (400 na API e mensagem idêntica na página), 121 caracteres, listagem em ordem alfabética, consulta inexistente (404) e `/condominios/<id>/` redirecionando para os apartamentos. Verificar que os testes falham antes da implementação.
- [x] 3.4 Implementar `condominiums/repository.py`, `condominiums/features/{create,list,get}_condominium.py` (handler + `APIView` + view HTML), `condominiums/urls.py`, `condominiums/templates/condominiums/{list,form}.html` e registrar as rotas de D8 em `config/urls.py`, incluindo o redirect de `/`. Verificar com `pytest tests/condominiums` e `tests/test_smoke.py` passando.

## 4. Capability `apartamentos`

- [x] 4.1 Escrever `tests/apartments/test_domain.py` (`normalize_text` com espaços e vazio → `None`; `natural_key` ignorando maiúsculas e tratando ausentes como iguais; todas as branches) e `tests/apartments/test_inputs.py` (número obrigatório e só espaços; número com 11 caracteres; torre com 21; andar 201, -6, "terceiro" e "3"; campo `tenant` extra ignorado). Verificar que os testes falham antes da implementação.
- [x] 4.2 Implementar `apartments/domain.py` (`Apartment`, `normalize_text`, `natural_key`, `DuplicateApartmentError`) e `apartments/inputs.py` (`ApartmentInput`) conforme D4 e D6. Verificar com `pytest tests/apartments/test_domain.py tests/apartments/test_inputs.py` passando e 100% de linhas e branches em `apartments/domain.py`.
- [x] 4.3 Escrever `tests/apartments/test_repository.py`: unicidade por torre+bloco+número sem diferenciar maiúsculas e com ausentes iguais; mesmo número em outra torre e em outro condomínio permitido; `IntegrityError` da constraint convertido em `DuplicateApartmentError` (mitigação do risco de corrida); ordenação com ausentes primeiro e número lexicográfico ("101" antes de "12"). Verificar que os testes falham antes da implementação.
- [x] 4.4 Implementar `apartments/models.py` (herda `TenantOwnedModel`, PK UUID, constraint `uniq_apartment_per_tenant` por expressão, ordenação de D5), a migração `apartments/migrations/0001_initial.py` e `apartments/repository.py` (só via `for_tenant`, mapeamento entidade ↔ model). Verificar com `pytest tests/apartments/test_repository.py` passando e `python manage.py makemigrations --check` sem pendências.
- [x] 4.5 Escrever `tests/apartments/test_api.py` e `tests/apartments/test_pages.py`, cobrindo cada cenário de `specs/apartamentos/spec.md`: criação completa e só com número (201), validações (400 com `{"errors": {"number": [...]}}`), duplicidade na criação e na edição (400, apartamento inalterado), listagem ordenada e vazia ("Nenhum apartamento cadastrado"), edição válida (200), `tenant` no corpo ignorado, exclusão (204 e confirmação na página), 404 para inexistente, isolamento (consulta, edição, exclusão e listagem cruzadas entre condomínios, todas com 404 ou sem vazamento) e formulário reexibido com os valores e a mensagem junto ao campo. Verificar que os testes falham antes da implementação.
- [x] 4.6 Implementar `apartments/features/{list,create,get,update,delete}_apartment.py` (handlers + `APIView` + views HTML, todas iniciando por `tenancy.public.get_condominium_or_404`), `apartments/urls.py` e `apartments/templates/apartments/{list,form,confirm_delete}.html`, e incluir as rotas de D8 em `config/urls.py`. Verificar com `pytest tests/apartments` passando.

## 5. Verificação integrada e documentação

- [x] 5.1 Rodar a suíte completa com cobertura no ambiente local: `docker compose run --rm web pytest --cov --cov-config=.coveragerc`. Verificar que todos os testes passam e que o relatório mostra 100% de linhas e branches em `condominiums/domain.py` e `apartments/domain.py`.
- [x] 5.2 Escrever `docs/verificacao-navegador/cadastro-de-apartamentos.md`, um roteiro passo a passo dos cenários de interface das duas specs (criar condomínio, criar/editar/excluir apartamento, erros de validação com valores preservados, duplicidade, lista vazia, URL de outro condomínio retornando 404). Executar o roteiro em `http://localhost:8000/` e registrar no arquivo a data, o navegador e o resultado de cada passo. Verificar que todos os passos estão marcados como OK.
- [x] 5.3 Criar `README.md` com como subir (`cp .env.example .env`, `docker compose up`), como testar (`docker compose run --rm web pytest`), as rotas de D8 e o aviso de que não há autenticação (ADR-0005). Verificar seguindo o README do zero, numa cópia limpa do repositório, até ver a listagem de condomínios.
- [x] 5.4 Abrir PR para `main` (GitHub Flow) e verificar que o workflow `ci.yml` termina verde.

## 6. ADRs

- [x] 6.1 Revisar `openspec/adrs/0013-resolucao-do-tenant-por-url.md` e `openspec/adrs/0014-estrutura-de-uma-fatia.md` (no store `tarefas`) contra o código implementado, ajustar o que divergir e promovê-las de `Proposed` para `Accepted` com aprovação do responsável. Verificar que o frontmatter das duas mostra `status: Accepted`.

## Workflow follow-up

- Rodar `/opsx:verify` e depois `/opsx:archive` quando o PR estiver aprovado com CI verde.
- Após o arquivamento, conferir `openspec/specs/condominios/spec.md` e `openspec/specs/apartamentos/spec.md` e atualizar a tabela de Capabilities do `openspec/project.md`.
