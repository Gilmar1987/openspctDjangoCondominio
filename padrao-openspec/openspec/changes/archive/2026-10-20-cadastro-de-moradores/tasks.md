# Tasks

Repositório de código: `C:\openspec\tarefas`. Trabalhar na branch `feat/cadastro-de-moradores` a partir da `main` atualizada (GitHub Flow). Comandos de verificação: seção "Comandos de verificação" do `project.md`.

## 1. Base Pessoa extensível e domínio do morador

- [x] 1.1 Estender `tests/people/test_domain.py`: uma subclasse com campo próprio obrigatório recebe o campo via `create(..., campo=...)` e `update(..., campo=...)` sem redefinir os métodos, e `Owner` continua funcionando sem campos próprios. Escrever `tests/residents/test_domain.py`: `Resident` é subclasse de `Person` e não redeclara `name`/`cpf`/`email`/`phone`; `ROLE_LABEL == "morador"`; `create`/`update` com `apartment_id`; `apartment_id` ausente → `InvalidResidentError`; `DuplicateCpfError("morador")` → "Já existe morador com este CPF neste condomínio.". Verificar que os testes novos falham antes da implementação.
- [x] 1.2 Implementar o repasse de `**own` em `people/domain.py` (D2) e criar `residents/__init__.py`, `apps.py` e `domain.py` (`Resident(Person)`, `InvalidResidentError`); registrar `residents` em `INSTALLED_APPS` e em `BUSINESS_APPS` de `tests/test_architecture.py`. Verificar com `pytest tests/people tests/residents tests/owners/test_domain.py tests/test_architecture.py` passando e 100% em `people/domain.py` e `residents/domain.py`.

## 2. Entrada, persistência e contratos públicos

- [x] 2.1 Escrever `tests/residents/test_inputs.py` (`ResidentInput` herda de `PersonInput` e só acrescenta `apartment_id`; ausente → "O campo apartamento é obrigatório."; UUID inválido → "O apartamento não foi encontrado neste condomínio."), `tests/residents/test_repository.py` (CPF só cifrado no banco; CPF único entre moradores do condomínio; mesmo CPF em outro condomínio permitido; listagem alfabética; isolamento por condomínio; `count_by_apartment`; `residences_by_cpf_hash`) e os testes de `owners_by_cpf_hash` e `get_owner_person` em `tests/owners/test_public.py`. Verificar que falham antes da implementação.
- [x] 2.2 Implementar `residents/inputs.py`, `models.py` (FK `PROTECT`, D3) + migração `residents/migrations/0001_initial.py`, `repository.py` e `public.py` (D4), e os acréscimos em `owners/public.py` e `owners/repository.py`. Acrescentar a fixture `make_resident` em `tests/conftest.py`. Verificar com os testes do grupo passando e `python manage.py makemigrations --check --dry-run` sem pendências.

## 3. Apartamentos: quantidade de moradores e bloqueio da exclusão (delta `apartamentos`)

- [x] 3.1 Escrever testes em `tests/apartments/test_residents_link.py`: `resident_count` na API (2 e 0) e a coluna na listagem; exclusão de apartamento com moradores recusada na API (400 com `{"errors": {"apartment": [...]}}`) e na página (aviso, sem botão Excluir; POST direto reexibe a mensagem), com apartamento e moradores intactos; `ProtectedError` simulado convertido na mesma mensagem; exclusão sem moradores continua funcionando. Ajustar os testes existentes que comparam o JSON inteiro de apartamento. Verificar que os testes novos falham antes da implementação.
- [x] 3.2 Implementar em `apartments/features/{__init__,list_apartments,delete_apartment}.py` e nos templates `list.html`/`confirm_delete.html` (D6). Verificar com `pytest tests/apartments tests/test_architecture.py` passando.

## 4. Cadastro de moradores (capability `moradores`)

- [x] 4.1 Escrever `tests/residents/test_api.py` e `tests/residents/test_pages.py` cobrindo cada cenário de `specs/moradores/spec.md`: campos e validações; vários moradores no mesmo apartamento; apartamento de outro condomínio ou inexistente; mudança de apartamento; proprietário morando em apartamento que não é seu; mesma pessoa em outro apartamento do condomínio (rejeitada); mesmo CPF em outro condomínio; CPF mascarado na listagem e completo só no GET individual e no formulário de edição; logs sem dados pessoais (`caplog`); listagem alfabética com apartamento; lista vazia ("Nenhum morador cadastrado"); morador reconhecido como proprietário ("também é proprietário (2 apartamentos)", `also_owner` na API); sem vínculo; proprietário de outro condomínio não reconhecido; pré-preencher a partir do proprietário (GET `?proprietario=` preenche e não grava); edição; exclusão sem afetar o proprietário; acesso cruzado → 404; erro de validação na API e na página. Verificar que falham antes da implementação.
- [x] 4.2 Implementar `residents/features/*.py` (handlers, `APIView`, views HTML, logs de D7, reconhecimento de D5), `residents/urls.py`, os templates `residents/templates/residents/{list,form,detail,confirm_delete}.html`, as rotas em `config/urls.py` e o link "Moradores" em `condominiums/templates/condominiums/list.html` e nos cabeçalhos de apartamentos e proprietários. Verificar com `pytest tests/residents` passando.

## 5. Proprietário que também é morador (delta `proprietarios`)

- [x] 5.1 Escrever testes em `tests/owners/test_resident_of.py`: `resident_of` com o apartamento na API (listagem e consulta) e "também é morador de <label>" nas páginas, quando o mesmo CPF é morador no condomínio; `null` e sem indicação quando não é; morador de outro condomínio não conta. Ajustar os testes existentes que comparam o JSON inteiro de proprietário. Verificar que os testes novos falham antes da implementação.
- [x] 5.2 Implementar em `owners/features/{__init__,list_owners,get_owner}.py` e nos templates `owners/{list,detail}.html` (D5). Verificar com `pytest tests/owners tests/test_architecture.py` passando.

## 6. Verificação integrada e documentação

- [x] 6.1 Rodar a suíte completa conforme os "Comandos de verificação" (testes com cobertura e checagem de migrações). Verificar que todos os testes passam, que há 100% em todos os `*/domain.py` (incluindo `residents/domain.py`) e que não há migração pendente.
- [x] 6.2 Escrever `docs/verificacao-navegador/cadastro-de-moradores.md` (roteiro dos cenários de interface das três deltas, incluindo pré-preenchimento, reconhecimento cruzado e bloqueio da exclusão de apartamento) e atualizar os roteiros de apartamentos e proprietários para as colunas novas. Executar os roteiros no navegador e registrar data, navegador, executor e resultado, indicando que a execução automatizada é cobertura fora da suíte. Verificar que todos os passos estão OK.
- [x] 6.3 Atualizar o `README.md`: rotas de moradores, a regra "um apartamento por morador no condomínio", o reconhecimento morador ↔ proprietário pelo CPF (sem sincronizar dados), e o DELETE de apartamento com moradores respondendo 400. Verificar seguindo o README numa cópia limpa até cadastrar um proprietário que também é morador e ver o vínculo nos dois sentidos.
- [x] 6.4 Fazer commit com o trailer `OpenSpec-Change: cadastro-de-moradores` e push da branch, e abrir o PR para `main` (push só com o pedido explícito do responsável, conforme as skills atualizadas). Verificar que o workflow `ci.yml` termina verde.

## 7. ADRs

- [x] 7.1 Revisar `openspec/adrs/0017-mesma-pessoa-entre-cadastros-pelo-hash-do-cpf.md` (store `tarefas`) contra o código implementado (consultas por hash nos `public.py`, nenhuma decifração no reconhecimento, sem sincronização) e promovê-la de `Proposed` para `Accepted` com aprovação explícita do responsável. Verificar que o frontmatter mostra `status: Accepted`.

## Workflow follow-up

- Após aprovação e merge do PR: `/opsx:verify` e `/opsx:archive` (cria a spec `moradores`, acrescenta um requisito e modifica "Excluir apartamento" em `apartamentos`, e acrescenta um requisito em `proprietarios`).
- Atualizar a tabela de Capabilities do `openspec/project.md` no arquivamento.
