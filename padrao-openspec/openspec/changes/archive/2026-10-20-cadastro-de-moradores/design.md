# Design

## Context

A `main` (`7e36c07`) já tem `people` (base `Person` / `PersonModel` / `PersonInput`, ADR-0016), `owners` (`Owner(Person)`), `apartments` (com `owner_id` e `public.py`) e `tenancy`. Os apps se comunicam só por `public.py` (ADR-0015), e `tests/test_architecture.py` confere isso. A motivação está em proposal.md, e o comportamento nas specs `moradores`, `apartamentos` (delta) e `proprietarios` (delta).

Pontos do código que esta change estende:
- `people/domain.py:84-89`: `Person.create(cls, tenant_id, name, cpf, email, phone)` e `update(...)` constroem `cls(...)` só com os atributos gerais. Hoje uma subclasse com atributos próprios obrigatórios não conseguiria usá-los.
- `apartments/features/delete_apartment.py:13`: `handle` exclui sem checar dependências.
- `owners/features/__init__.py:53,64`: `list_json` / `detail_json` montam as respostas de proprietário.
- `PersonModel.hash_cpf` (`people/models.py`) já calcula o HMAC do CPF.

## Architecture Decisions

- **ADR-0017** (`openspec/adrs/0017-mesma-pessoa-entre-cadastros-pelo-hash-do-cpf.md`, **Proposed**): a mesma pessoa é reconhecida entre cadastros pelo `cpf_hash` no mesmo condomínio, sem decifrar CPF e sem sincronizar dados. Precisa ser promovida a `Accepted` antes do arquivamento (tarefa 7.1).
- Aplicadas sem alteração: ADR-0015 (só `public.py`), ADR-0016 (`Resident(Person)`, herança por model abstrato) e ADR-0009 (CPF cifrado, logs sem dados pessoais).

## Goals / Non-Goals

**Goals:**
- O app `residents` segue o mesmo molde de `owners` (ADR-0014 / ADR-0016).
- A base `Person` passa a aceitar atributos próprios das subclasses sem que cada subclasse reimplemente `create`/`update`.
- O reconhecimento cruzado proprietário ↔ morador funciona sem nenhuma decifração.
- O bloqueio da exclusão de apartamento com moradores vale na aplicação e no banco.

**Non-Goals:**
- Sincronizar dados entre os cadastros da mesma pessoa.
- Paginação e busca de moradores.
- Pré-preenchimento pela API: ele é só uma conveniência da página.

## Decisions

### D1. Layout
```
residents/   domain.py (Resident(Person)), models.py (ResidentRecord(PersonModel)), inputs.py (ResidentInput(PersonInput)),
             repository.py, public.py, features/{list,create,get,update,delete}_resident.py, features/__init__.py,
             urls.py, templates/residents/{list,form,detail,confirm_delete}.html
people/      domain.py: create/update aceitam atributos próprios da subclasse (D2)
apartments/  features: resident_count na listagem/API; bloqueio na exclusão (D6); template list/confirm_delete
owners/      public.py: owners_by_cpf_hash, get_owner_person; features: resident_of (D5)
config/      settings (INSTALLED_APPS), urls (rotas de moradores)
tests/residents/**, tests/people (extensão), tests/apartments, tests/owners, tests/test_architecture.py (+ residents)
```

### D2. Extensão da base Pessoa (ADR-0016)
`Person.create(cls, tenant_id, name, cpf, email=None, phone=None, **own)` e `update(self, *, name, cpf, email, phone, **own)` repassam `**own` para `cls(...)` e para `replace(...)`. As subclasses só declaram os campos próprios e validam esses campos no `__post_init__`. O comportamento de `Owner`, sem campos próprios, não muda.
- `Resident(Person)`: `ROLE_LABEL = "morador"` e o campo `apartment_id: UUID`. O `__post_init__` levanta `InvalidResidentError` se o `apartment_id` for `None`.
*Alternativa:* `Resident` sobrescrever `create`/`update`. Foi descartada porque duplicaria a normalização da base, o que a ADR-0016 proíbe.

### D3. Persistência
- `ResidentRecord(PersonModel)`, tabela `resident`. Herda os campos e a constraint `residents_residentrecord_uniq_cpf_per_tenant` (CPF único por condomínio entre moradores, e daí "um apartamento por morador no condomínio").
- `apartment = ForeignKey("apartments.ApartmentRecord", on_delete=PROTECT, db_column="apartment_id", related_name="+")`, declarada por string (ADR-0015). O `PROTECT` é a segunda linha de defesa do bloqueio da exclusão (D6).
- O repositório segue o de `owners`: `add`, `update`, `get`, `list_for_tenant` (ordem por `Lower(name)`), `cpf_taken`, `delete`, `count_by_apartment`, `residences_by_cpf_hash`, sempre via `for_tenant`, com conversão de `IntegrityError` em `DuplicateCpfError("morador")`.

### D4. Contratos públicos
- `residents/public.py`:
  - `count_by_apartment(tenant_id) -> dict[UUID, int]`;
  - `count_in_apartment(tenant_id, apartment_id) -> int`;
  - `residences_by_cpf_hash(tenant_id, hashes) -> dict[str, UUID]` (hash → apartamento onde mora).
- `owners/public.py` (acréscimos):
  - `owners_by_cpf_hash(tenant_id, hashes) -> dict[str, OwnerRef]`;
  - `get_owner_person(tenant_id, owner_id) -> OwnerPerson | None` (nome, CPF, e-mail e telefone; usado só no pré-preenchimento, a exceção prevista na ADR-0017).
- O hash vem sempre de `PersonModel.hash_cpf` (`people.models`, import permitido pela ADR-0016).

### D5. Reconhecimento cruzado (ADR-0017)
- **Moradores:** na listagem e na consulta, o handler coleta os `cpf_hash` dos moradores, chama `owners.public.owners_by_cpf_hash` e conta os apartamentos com `apartments.public.count_by_owner`. As respostas trazem:
  - API: `also_owner: {"owner_id", "apartment_count"} | null`;
  - página: "também é proprietário (N apartamentos)".
- **Proprietários:** `list_json` / `detail_json` ganham `resident_of: {"id", "label"} | null`, via `residents.public.residences_by_cpf_hash` mais `apartments.public.get_many`. As páginas mostram "também é morador de <label>".
- Cada listagem faz uma consulta extra com `IN (hashes)`, uma por página e não por linha.

### D6. Bloqueio da exclusão de apartamento
- `delete_apartment.handle` chama `residents.public.count_in_apartment`. Se o resultado for maior que zero, levanta `ApartmentHasResidentsError(n)`, com a mensagem "Este apartamento tem N morador(es) e precisa ficar sem moradores antes de ser excluído.".
  - API: 400 `{"errors": {"apartment": [msg]}}`.
  - Página de confirmação: mostra o aviso e esconde o botão "Excluir". Um POST direto reexibe a página com a mensagem.
- Um `ProtectedError` do banco (corrida) é convertido na mesma mensagem.

### D7. Entrada e páginas de moradores
- `ResidentInput(PersonInput)` acrescenta `apartment_id: UUID` obrigatório.
  - Ausente: "O campo apartamento é obrigatório.".
  - UUID inválido ou apartamento não encontrado no condomínio (checado no handler via `apartments.public.get_many`): "O apartamento não foi encontrado neste condomínio.".
- O formulário tem um `<select>` com todos os apartamentos do condomínio (rótulo de `apartments.public`) e, no "novo", um seletor "Preencher a partir do proprietário". Esse seletor faz um GET `?proprietario=<id>` e preenche nome, CPF, e-mail e telefone via `owners.public.get_owner_person`, sem gravar nada.
- As rotas `condominios/<id>/moradores/` (lista, `novo/`, `<id>/`, `<id>/editar/`, `<id>/excluir/`) e `api/condominios/<id>/moradores/` (GET/POST, GET/PUT/DELETE) seguem o mesmo formato de proprietários.
- Os logs registram só `resident rejected tenant=<id> fields=[...]` (ADR-0009).

## Risks / Trade-offs

- **[Dados pessoais de moradores sem autenticação]** → Mesma proteção de proprietários (cifra, máscara, logs, testes) e aviso no README.
- **[Exposição de dados do proprietário no pré-preenchimento]** → Só na página, só no mesmo condomínio, só por ação explícita do usuário (GET com o id). O CPF vai para o campo de edição, o único lugar onde o CPF completo já aparece. Coberto por teste.
- **[Esquema novo e FK com PROTECT]** → Migração aditiva. O `PROTECT` impede exclusão acidental. A checagem na aplicação dá a mensagem amigável, e o `ProtectedError` é convertido nela (teste).
- **[Quebra no DELETE de apartamento com moradores (204 → 400)]** → Documentado na proposal e no README. Não afeta dados atuais, porque ainda não existem moradores.
- **[Reconhecimento cruzado depende da mesma `CPF_HASH_KEY`]** → Chave única no `.env` (ADR-0017). Teste que cria proprietário e morador com o mesmo CPF e confere o vínculo nos dois sentidos.
- **[Dados divergentes entre cadastros da mesma pessoa]** → Risco aceito (ADR-0016, ADR-0017), registrado no README.

**Raio de impacto**
- Arquivos-alvo:
  - **novos:** `residents/**`, `tests/residents/**`, `residents/migrations/0001_initial.py`, `docs/verificacao-navegador/cadastro-de-moradores.md`, `openspec/adrs/0017-...md` (store);
  - **alterados:** `people/domain.py`, `owners/public.py`, `owners/features/{__init__,list_owners,get_owner}.py`, `owners/templates/owners/{list,detail}.html`, `apartments/features/{__init__,list_apartments,delete_apartment}.py`, `apartments/templates/apartments/{list,confirm_delete}.html`, `condominiums/templates/condominiums/list.html` (link "Moradores"), `config/{settings,urls}.py`, `tests/test_architecture.py`, `tests/conftest.py` (fixture `make_resident`), `README.md`, `docs/verificacao-navegador/cadastro-de-{apartamentos,proprietarios}.md`.
- Dependentes afetados:
  - testes de API de apartamentos e proprietários que comparam o JSON inteiro (ganham `resident_count` / `resident_of`);
  - o teste de exclusão de apartamento (continua válido sem moradores);
  - os roteiros de navegador de apartamentos e proprietários (colunas novas).

## Migration Plan

`docker compose up -d --build` aplica `residents/0001`. Rollback: `python manage.py migrate residents zero` e reverter o commit. Não há dados existentes afetados.

## Open Questions

- Nenhuma que mude specs, abordagem ou tarefas.
