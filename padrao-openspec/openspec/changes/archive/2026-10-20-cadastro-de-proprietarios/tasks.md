# Tasks

Repositório de código: `C:\openspec\tarefas`. Trabalhar na branch `feat/cadastro-de-proprietarios` a partir da `main` (GitHub Flow).

## 1. Configuração e plataforma (crypto, logs, fronteiras)

- [x] 1.1 Adicionar `cryptography==50.0.2` ao `requirements.txt`; exigir `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY` em `config/settings.py`; adicioná-las ao `.env.example` (placeholders + comando de geração da chave Fernet), ao `.github/workflows/ci.yml` (valores de teste fixos) e ao `.env` local com chaves geradas (D10). Verificar com `docker compose up -d --build` e `python manage.py check` sem erros, e com `check` falhando sem `FIELD_ENCRYPTION_KEY`.
- [x] 1.2 Escrever `tests/shared/test_crypto.py` (`encrypt`/`decrypt` ida e volta; o token não contém o texto; `keyed_hash` determinístico e diferente para entradas diferentes) e `tests/shared/test_logging.py` (`PersonalDataFilter` mascara CPF com e sem máscara, e-mail e telefone em `msg` e `args`). Verificar que os testes falham antes da implementação.
- [x] 1.3 Implementar `shared/crypto.py` (D4) e `shared/logging.py`, e configurar `LOGGING` em `config/settings.py` com o filtro no handler de console (D9). Verificar com `pytest tests/shared` passando.
- [x] 1.4 Escrever `tests/test_architecture.py` (AST): nenhum app (`owners`, `apartments`, `condominiums`) importa outro app fora de `<app>.public`, `tenancy.public`, `shared.*` e `people.{domain,models,inputs}` (ADR-0015, ADR-0016), e `people` não importa nenhum app de negócio. Verificar que o teste passa no código atual e falha quando se acrescenta temporariamente `from apartments import models` em `condominiums/domain.py`, removendo depois a linha.

## 2. Domínio e entrada de proprietários

- [x] 2.1 Escrever `tests/people/test_domain.py` (classe base, ADR-0016): `only_digits`; `is_valid_cpf` ("52998224725" válido, "52998224726" inválido, "11111111111" inválido, tamanhos errados); `mask_cpf` → "***.982.247-**"; `format_phone`; `Person.create`/`update` normalizando nome, CPF, e-mail e telefone; `create`/`update` chamados numa subclasse devolvem a subclasse; cobrir todas as branches. Escrever também `tests/people/test_inputs.py`: nome obrigatório e com limite de 120; CPF ausente, com máscara e inválido; e-mail inválido ("maria@") e válido; telefone "1234" inválido e "(81) 99999-0000" → "81999990000"; brancos viram ausentes; mensagens pt-BR. Verificar que os testes falham antes da implementação.
- [x] 2.2 Implementar `people/__init__.py`, `people/apps.py`, `people/domain.py` e `people/inputs.py` (D5), e registrar `people` em `INSTALLED_APPS`. Verificar com `pytest tests/people` passando e 100% de linhas e branches em `people/domain.py`.
- [x] 2.3 Escrever `tests/owners/test_domain.py` (`Owner` é subclasse de `Person` e herda `create`/`update` sem redefinir atributos; `plan_apartment_links`: vincular livres, manter os próprios, liberar os retirados, `ApartmentNotFoundError`, `ApartmentTakenError`, todas as branches) e `tests/owners/test_inputs.py` (`OwnerInput` herda as validações de `PersonInput` e acrescenta `apartment_ids` vindo de lista JSON e de `QueryDict.getlist`; UUID inválido → "Apartamento inválido."). Verificar que os testes falham antes da implementação.
- [x] 2.4 Implementar `owners/__init__.py`, `owners/apps.py`, `owners/domain.py` (`Owner(Person)`) e `owners/inputs.py` (`OwnerInput(PersonInput)`), e registrar `owners` em `INSTALLED_APPS`. Verificar com `pytest tests/owners/test_domain.py tests/owners/test_inputs.py` passando, 100% em `owners/domain.py`, e por inspeção (`grep`) que `owners/domain.py` e `owners/inputs.py` não redeclaram `name`, `cpf`, `email` nem `phone`.

## 3. Persistência e contratos públicos

- [x] 3.1 Escrever `tests/owners/test_repository.py` (CPF gravado só cifrado, com leitura do valor bruto da coluna `cpf_encrypted` sem "52998224725"; unicidade de CPF por condomínio via `cpf_hash` e `IntegrityError` convertido em `DuplicateCpfError`; mesmo CPF em outro condomínio permitido; listagem alfabética; `for_tenant` isolando condomínios) e `tests/apartments/test_public.py` (`list_selectable_for_owner`, `list_by_owner`, `count_by_owner`, `get_many`, `assign_owner` condicional, que não toma apartamento de outro dono, e `release_owner` com `keep_ids`, todos restritos ao condomínio). Verificar que os testes falham antes da implementação.
- [x] 3.2 Implementar `people/models.py` (`PersonModel` abstrato com `set_cpf`/`get_cpf` e a constraint de CPF por condomínio, D3), `owners/models.py` (`OwnerRecord(PersonModel)`) + migração `owners/migrations/0001_initial.py`, `owners/repository.py` e `owners/public.py` (D2, D3), e acrescentar `owner` FK `SET_NULL` em `apartments/models.py` + migração `apartments/migrations/0002_*.py`, mais `apartments/public.py` e as funções de repositório que ele usa. Verificar com `pytest tests/owners/test_repository.py tests/apartments/test_public.py tests/test_architecture.py` passando e `python manage.py makemigrations --check` sem pendências.

## 4. Apartamento com proprietário (capability `apartamentos`)

- [x] 4.1 Atualizar os testes de `tests/apartments/` para os cenários de `specs/apartamentos/spec.md` (delta): criar com proprietário; trocar; remover; proprietário de outro condomínio ou inexistente → 400 com `owner_id` e nada gravado; select do formulário com "Sem proprietário" + proprietários de C em ordem alfabética, sem CPF; listagem com nome ou "—"; API com `owner_id`/`owner_name`. Ajustar os testes existentes que comparam o JSON inteiro. Verificar que os testes novos falham antes da implementação e que os demais continuam passando.
- [x] 4.2 Implementar `owner_id` em `apartments/domain.py`, `inputs.py`, `repository.py`, `features/*.py` (validação via `owners.public.get_owner`, nomes via `names_by_id`) e nos templates `list.html`/`form.html` (D5, D6, D8). Verificar com `pytest tests/apartments tests/test_architecture.py` passando e 100% em `apartments/domain.py`.

## 5. Cadastro de proprietários (capability `proprietarios`)

- [x] 5.1 Escrever `tests/owners/test_api.py` e `tests/owners/test_pages.py` cobrindo cada cenário de `specs/proprietarios/spec.md`: campos e validações (400 com mensagens pt-BR); CPF duplicado e o mesmo CPF em outro condomínio; CPF mascarado na listagem (página e API, sem o CPF completo no HTML/JSON) e completo só no GET individual e no formulário de edição; listagem alfabética com quantidade; consulta com apartamentos; lista vazia ("Nenhum proprietário cadastrado"); vincular N, retirar do conjunto, apartamento de outro dono (rejeitado e inalterado), de outro condomínio ou inexistente; opções do formulário (livres + próprios); edição; exclusão com desvinculação (os apartamentos continuam e ficam sem dono); página de confirmação com a contagem; acesso cruzado → 404; formulário reexibido com valores e mensagem junto ao CPF; teste com `caplog` de criação rejeitada sem nome/CPF/e-mail/telefone no log. Verificar que os testes falham antes da implementação.
- [x] 5.2 Implementar `owners/features/*.py` (handlers + `APIView` + views HTML, transações de D7, eventos de log de D9), `owners/urls.py`, os templates `owners/templates/owners/{list,form,detail,confirm_delete}.html`, as rotas em `config/urls.py` (D8) e o link "Proprietários" em `condominiums/templates/condominiums/list.html` e nos cabeçalhos de apartamentos. Verificar com `pytest tests/owners` passando.
- [x] 5.3 Escrever um teste de corrida em `tests/owners/test_api.py`: o apartamento é tomado por outro dono entre a checagem e a escrita (simulado com `mock` em `apartments.public.get_many`), a transação é desfeita e o proprietário não é criado (mitigação do risco de corrida de D7). Verificar com `pytest tests/owners/test_api.py -k corrida` passando.

## 6. Verificação integrada e documentação

- [x] 6.1 Rodar a suíte completa com cobertura: `docker compose run --rm web pytest --cov --cov-config=.coveragerc`. Verificar que todos os testes passam e que há 100% em `people/domain.py`, `owners/domain.py`, `apartments/domain.py` e `condominiums/domain.py`.
- [x] 6.2 Escrever `docs/verificacao-navegador/cadastro-de-proprietarios.md` (roteiro dos cenários de interface das duas deltas) e atualizar o passo 9 de `docs/verificacao-navegador/cadastro-de-apartamentos.md` para a coluna Proprietário. Executar os dois roteiros no navegador em `http://localhost:<WEB_PORT>/` e registrar data, navegador e resultado em cada arquivo. Verificar que todos os passos estão OK.
- [x] 6.3 Atualizar o `README.md`: rotas de proprietários, as duas chaves novas no `.env` e como gerá-las, o aviso de dados pessoais (só dados de teste) e a consequência de perder a chave. Verificar seguindo o README numa cópia limpa até cadastrar um proprietário com dois apartamentos.
- [x] 6.4 Fazer commit com o trailer `OpenSpec-Change: cadastro-de-proprietarios`, push da branch e PR para `main`. Verificar que o workflow `ci.yml` termina verde.

## 7. ADRs

- [x] 7.1 Revisar `openspec/adrs/0016-pessoa-como-base-herdada.md` (store `tarefas`) contra o código implementado (`people/`, `Owner(Person)`, `OwnerRecord(PersonModel)`, `OwnerInput(PersonInput)`), ajustar o que divergir e promovê-la de `Proposed` para `Accepted` com aprovação explícita do responsável. Verificar que o frontmatter mostra `status: Accepted`.

## Workflow follow-up

- Após aprovação e merge do PR: `/opsx:verify` e `/opsx:archive` (a spec `apartamentos` recebe os 2 requisitos adicionados e é criada a spec `proprietarios`).
- Atualizar a tabela de Capabilities do `openspec/project.md` no arquivamento.
