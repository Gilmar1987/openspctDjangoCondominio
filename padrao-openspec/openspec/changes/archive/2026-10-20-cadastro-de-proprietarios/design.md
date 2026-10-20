# Design

## Context

O código em `C:\openspec\tarefas` (main em `0d70628`) já tem as fatias `condominiums` e `apartments`, a plataforma `tenancy` e o pacote `shared` (tradução de erros Pydantic, respostas JSON e o roteador `api_route`). Hoje `apartments` não conhece o conceito de proprietário. A motivação está em proposal.md (Why) e o comportamento nas specs `proprietarios` e `apartamentos`.

Restrições vigentes:
- ADR-0001: Vertical Slice e domínio rico. A regra de comunicação foi substituída pela ADR-0015.
- ADR-0004: Django ORM.
- ADR-0005: sem autenticação.
- ADR-0007 e ADR-0013: `tenant_id` e `for_tenant()`.
- ADR-0009: anonimização em logs, criptografia de campos sensíveis com chave em variável de ambiente e hash determinístico para unicidade.
- ADR-0012 e ADR-0014: Pydantic, `domain.py` puro com 100% de cobertura, `APIView` sem `Serializer`.
- ADR-0015: contrato `public.py` entre apps e transação única.

## Architecture Decisions

- **ADR-0015** (`openspec/adrs/0015-contratos-publicos-entre-fatias.md`, **Accepted** em 2026-10-19): `owners` e `apartments` se comunicam só pelos `public.py` um do outro, e a exclusão com desvinculação roda numa única transação. É a primeira change a aplicá-la.
- **ADR-0016** (`openspec/adrs/0016-pessoa-como-base-herdada.md`, **Proposed**): o pacote de plataforma `people` concentra a base de pessoa (`Person`, `PersonModel` abstrato, `PersonInput`). `Owner` herda dela, e as futuras entidades de pessoa também herdarão. A ADR precisa ser promovida a `Accepted` antes do arquivamento (tarefa 7.1).
- A escolha da biblioteca de criptografia (D4) é local e cumpre a ADR-0009 sem alterá-la.

## Goals / Non-Goals

**Goals:**
- Novo app `owners` com a mesma estrutura de fatia da ADR-0014.
- Vínculo 1:N com consistência transacional e validação de condomínio dos dois lados.
- CPF protegido de ponta a ponta: validação, criptografia, hash para unicidade, máscara na exibição e ausência nos logs.
- Teste automatizado das fronteiras entre apps (ADR-0015).

**Non-Goals:**
- Rotação de chave de criptografia (fica para uma change futura).
- Busca por CPF ou nome.
- FK composta `(tenant_id, owner_id)` no banco. A consistência de condomínio fica na aplicação (D6).

## Decisions

### D1. Layout
```
people/        apps.py, domain.py (Person + regras de CPF/e-mail/telefone), models.py (PersonModel abstrato),
               inputs.py (PersonInput) — plataforma, sem tabelas próprias (ADR-0016)
owners/        domain.py (Owner(Person)), models.py (OwnerRecord(PersonModel)), repository.py,
               inputs.py (OwnerInput(PersonInput)), public.py,
               features/{list_owners,create_owner,get_owner,update_owner,delete_owner}.py,
               features/__init__.py, urls.py, templates/owners/{list,form,detail,confirm_delete}.html
apartments/    + public.py; domain/models/inputs/repository/features/templates alterados
shared/        + crypto.py (Fernet + HMAC), logging.py (filtro de dados pessoais)
config/        settings.py (chaves e LOGGING), urls.py (rotas de owners)
tests/owners/, tests/apartments/ (novos casos), tests/shared/, tests/test_architecture.py
```

### D2. Contratos públicos (ADR-0015)
`owners/public.py`:
- `OwnerRef(id, name)`;
- `list_owners(tenant_id) -> list[OwnerRef]`, em ordem alfabética;
- `get_owner(tenant_id, owner_id) -> OwnerRef | None`;
- `names_by_id(tenant_id, ids) -> dict[UUID, str]`.

`apartments/public.py`:
- `ApartmentRef(id, label, owner_id)`, em que `label` é "Torre A · Bloco 1 · Nº 301";
- `list_selectable_for_owner(tenant_id, owner_id | None)`: apartamentos livres mais os do proprietário;
- `list_by_owner(tenant_id, owner_id)`;
- `count_by_owner(tenant_id) -> dict[UUID, int]`;
- `get_many(tenant_id, ids) -> dict[UUID, ApartmentRef]`;
- `assign_owner(tenant_id, apartment_ids, owner_id)`;
- `release_owner(tenant_id, owner_id, keep_ids=())`.

Todas as funções filtram por `for_tenant`. Os outros apps importam só esses módulos. `tests/test_architecture.py` percorre as importações (AST) de `owners`, `apartments` e `condominiums` e falha se qualquer um importar de outro app algo que não seja `<app>.public`, `tenancy.public`, `shared.*` ou `people.{domain,models,inputs}` (ADR-0016). O mesmo teste falha se `people` importar qualquer app de negócio.

### D3. Persistência
- `people/models.py`: `PersonModel(TenantOwnedModel)`, **abstrato** (ADR-0016), com os campos herdados:
  - `id` (UUID);
  - `name` (`CharField` de 120);
  - `cpf_encrypted` (`TextField`, token Fernet);
  - `cpf_hash` (`CharField` de 64, HMAC-SHA256 hex);
  - `email` (`CharField` de 254, null);
  - `phone` (`CharField` de 11, null).

  Ele traz os métodos `set_cpf(digits)` (cifra e calcula o hash) e `get_cpf()` (decifra), e `Meta.constraints` com `UniqueConstraint(F("tenant"), "cpf_hash", name="%(app_label)s_%(class)s_uniq_cpf_per_tenant")`, que o Django expande em cada tabela concreta.
- `owners/models.py`: `OwnerRecord(PersonModel)`, tabela `owner`. Não acrescenta campos: o vínculo com apartamentos é a FK do lado de `apartment`.
*Alternativa:* herança multi-tabela (tabela `person` + `owner`). Foi descartada pela ADR-0016.
- Em `apartment`, a coluna `owner` é `ForeignKey("owners.OwnerRecord", null=True, on_delete=SET_NULL, db_column="owner_id", related_name="+")`, declarada por string para não importar `owners.models`. A migração `apartments/0002` depende de `owners/0001`. O `SET_NULL` é uma segunda linha de defesa: a desvinculação explícita acontece em D7.
*Alternativa:* uma tabela de vínculo. Não foi escolhida porque a relação é 1:N e uma FK no apartamento já representa "no máximo um proprietário".

### D4. Criptografia e hash (ADR-0009)
- `shared/crypto.py`:
  - `encrypt(text) -> str` e `decrypt(token) -> str` usam `cryptography.fernet.Fernet(settings.FIELD_ENCRYPTION_KEY)`;
  - `keyed_hash(text) -> str` usa `hmac.new(settings.CPF_HASH_KEY, text, sha256).hexdigest()`.
- O hash é calculado sobre os 11 dígitos normalizados. É ele que garante a unicidade e a comparação: a busca nunca descriptografa a tabela.
- Dependência: `cryptography==50.0.2`.
*Alternativas:*
- `pgcrypto` no banco: não foi escolhido porque a chave iria para as queries e os logs do banco.
- Bibliotecas `django-*-fields`: não foram escolhidas porque são menos mantidas e escondem o mecanismo que a ADR-0009 pede explícito.

### D5. Domínio e validação
- `people/domain.py` (Python puro, 100% de cobertura, base herdada):
  - `only_digits`, `is_valid_cpf` (dígitos verificadores; rejeita sequências repetidas), `mask_cpf` (`***.982.247-**`), `format_phone`;
  - a dataclass `Person` (id, tenant_id, name, cpf, email, phone), com `create`/`update` que normalizam os atributos gerais e devolvem a própria subclasse (`cls(...)` / `dataclasses.replace`);
  - `InvalidPersonError` e `DuplicateCpfError`.
- `owners/domain.py` (Python puro, 100% de cobertura):
  - `Owner(Person)`, que herda os atributos e as regras sem reimplementá-los;
  - `plan_apartment_links(owner_id, requested_ids, found: dict[UUID, current_owner_id | None])`, que devolve `(to_assign, to_release)` ou levanta `ApartmentNotFoundError` / `ApartmentTakenError`.
- `people/inputs.py`: `PersonInput` (Pydantic) com:
  - `name` (1 a 120);
  - `cpf` (só dígitos, validado por `people.domain.is_valid_cpf`);
  - `email` (regex simples `^[^@\s]+@[^@\s]+\.[^@\s]+$`, até 254, sem a dependência `email-validator`);
  - `phone` (10 ou 11 dígitos);
  - `PERSON_LABELS` com os rótulos pt-BR desses campos.
- `owners/inputs.py`: `OwnerInput(PersonInput)` acrescenta `apartment_ids: list[UUID]`.

  No formulário HTML, `apartment_ids` vem de `QueryDict.getlist`. Na API, vem como lista JSON. As mensagens em pt-BR vêm de `shared.validation.to_ptbr_errors`, e os erros de UUID usam a mensagem "Apartamento inválido.".
- `apartments`:
  - `Apartment` ganha `owner_id: UUID | None`, aceito em `create`/`update`;
  - `ApartmentInput` ganha `owner_id: UUID | None` (texto vazio vira `None`).

### D6. Consistência de condomínio no vínculo
- Ao gravar um apartamento com `owner_id`, o handler chama `owners.public.get_owner(tenant_id, owner_id)`. Se o retorno for `None`, responde 400 `{"errors": {"owner_id": ["O proprietário não foi encontrado neste condomínio."]}}`.
- Ao gravar um proprietário, o handler chama `apartments.public.get_many(tenant_id, apartment_ids)` e `plan_apartment_links`. As mensagens são:
  - `apartment_ids`: "O apartamento não foi encontrado neste condomínio.";
  - `apartment_ids`: "O apartamento <label> já tem outro proprietário.".

### D7. Transações (ADR-0015)
- **Criar/editar proprietário:** dentro de `transaction.atomic()`, salva o proprietário e chama `apartments.public.assign_owner(...)` com `to_assign` e `release_owner(..., keep_ids=requested)`. Uma corrida que troque o dono de um apartamento entre a checagem e a escrita é coberta pelo `UPDATE ... WHERE owner_id IS NULL OR owner_id = <owner>`. Se a contagem atualizada for menor que a esperada, a transação é desfeita e a resposta é o erro de "já tem outro proprietário".
- **Excluir proprietário:** dentro de `atomic()`, chama `release_owner(tenant, owner_id)` e depois exclui o proprietário.

### D8. Exibição e API
- Listagem de proprietários: nome, CPF mascarado, e-mail, telefone formatado e quantidade de apartamentos.
- Página de detalhe `/condominios/<id>/proprietarios/<owner>/`: dados com o CPF mascarado e os apartamentos vinculados.
- O formulário de edição traz o CPF completo, como a spec permite.
- API:
  - `GET/POST /api/condominios/<id>/proprietarios/`: a listagem traz `cpf_masked`, `apartment_count` e nunca o CPF completo;
  - `GET/PUT/DELETE .../<owner>/`: o GET individual traz o `cpf` completo e `apartments: [{id, label}]`;
  - os códigos de resposta seguem a spec.
- Apartamentos: `as_json` ganha `owner_id` e `owner_name`, este último resolvido por `owners.public.names_by_id`. A listagem ganha a coluna "Proprietário", e o formulário ganha um `<select>` com "Sem proprietário" mais `list_owners`.
- Navegação: na lista de condomínios, "Apartamentos · Proprietários"; os cabeçalhos das páginas de um condomínio ganham links entre as duas.

### D9. Logs sem dados pessoais (ADR-0009)
- `shared/logging.py` define `PersonalDataFilter`, aplicado ao handler de console em `LOGGING`. Ele mascara padrões de CPF (`\d{3}\.?\d{3}\.?\d{3}-?\d{2}`), e-mail e telefone em `record.msg` e `record.args`.
- As fatias de `owners` registram eventos só com identificadores e nomes de campo, por exemplo `owner rejected tenant=<id> fields=[cpf]`, nunca com valores. O nome da pessoa não é detectável por regex. A proteção vem dessa regra, verificada por teste com `caplog`.

### D10. Configuração
- `settings.py` exige `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY`.
- O `.env.example` traz placeholders e o comando para gerar a chave Fernet.
- O `ci.yml` define valores de teste fixos, que não são segredos.
- O `.env` local precisa receber chaves geradas.

## Risks / Trade-offs

- **[Dados pessoais sem autenticação]** → Aviso no README e na proposal, só dados de teste, aplicação só local (ADR-0005, ADR-0006).
- **[Vazamento de CPF em listagens, logs ou banco]** → Máscara em todas as listagens (testes de API e de página), coluna criptografada (teste que lê o valor bruto do banco), `PersonalDataFilter` e eventos sem valores (teste com `caplog`).
- **[Perda ou troca da chave de criptografia]** → Os CPFs ficam ilegíveis. A chave fica no `.env`, fora do git. `docker compose down -v` apaga os dados junto, e a rotação de chave fica fora do escopo e documentada no README.
- **[Esquema novo e coluna nova em `apartment`]** → Migração aditiva (FK nula). Os apartamentos existentes ficam sem proprietário. `makemigrations --check` roda no CI.
- **[Proprietário de outro condomínio gravado via FK]** → Validação no handler (D6) e testes de acesso cruzado nos dois sentidos. A FK composta no banco fica fora do escopo.
- **[Corrida no vínculo]** → `UPDATE` condicional e transação (D7), com teste que simula o apartamento tomado entre a checagem e a escrita.
- **[Acoplamento entre apps]** → Só via `public.py`, com teste de arquitetura.

**Raio de impacto**
- Arquivos-alvo:
  - **novos:** `people/**`, `tests/people/**`, `openspec/adrs/0016-pessoa-como-base-herdada.md` (store), `owners/**`, `apartments/public.py`, `apartments/migrations/0002_*.py`, `shared/crypto.py`, `shared/logging.py`, `tests/owners/**`, `tests/test_architecture.py`, `tests/shared/test_crypto.py`, `tests/shared/test_logging.py`, `docs/verificacao-navegador/cadastro-de-proprietarios.md`;
  - **alterados:** `apartments/{domain,models,inputs,repository,urls}.py`, `apartments/features/*.py`, `apartments/templates/apartments/{list,form}.html`, `condominiums/templates/condominiums/list.html`, `config/{settings,urls}.py`, `requirements.txt`, `.env.example`, `.github/workflows/ci.yml`, `README.md`, testes de `apartments` existentes (fixtures ganham `owner_id`).
- Dependentes afetados:
  - testes atuais de API de apartamentos que comparam o JSON inteiro (`test_get_apartment`), que ganham `owner_id`/`owner_name`;
  - o roteiro `docs/verificacao-navegador/cadastro-de-apartamentos.md` (a listagem ganha a coluna Proprietário);
  - o `.env` local de cada desenvolvedor (novas variáveis obrigatórias).

## Migration Plan

1. Atualizar o `.env` com as duas chaves novas.
2. `docker compose up -d --build`, para instalar o `cryptography` e aplicar `owners/0001` e `apartments/0002`.

Rollback: reverter as migrações `apartments 0001` e `owners zero` e o commit. Os apartamentos não perdem dados, só o vínculo.

## Open Questions

- Rotação da chave de criptografia (recriptografar os CPFs). Não afeta esta change.
