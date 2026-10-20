---
id: ADR-0016
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: [cadastro-de-proprietarios]
---

# ADR-0016: Pessoa como classe base herdada por proprietário e futuras entidades de pessoa

## Contexto

O produto vai cadastrar mais de um tipo de pessoa: proprietários agora (change `cadastro-de-proprietarios`) e moradores depois. Todas compartilham os mesmos atributos gerais (nome, CPF, e-mail, telefone) e as mesmas regras: validação de CPF, criptografia e hash do CPF, máscara e anonimização em logs (ADR-0009). Sem uma base comum, cada entidade reimplementaria essas regras e a proteção de dados poderia divergir entre elas.

O responsável avaliou a alternativa de composição (Pessoa como cadastro único e proprietário/morador como papéis) e decidiu por herança: "proprietário continua mas vai herda da classe pessoa atributos gerais".

## Decisão

- Um pacote de plataforma `people` SHALL concentrar a base de pessoa:
  - `people/domain.py`: dataclass `Person` (id, tenant_id, name, cpf, email, phone) e regras puras de CPF, e-mail e telefone (validação, normalização, máscara);
  - `people/models.py`: model abstrato `PersonModel(TenantOwnedModel)` com `name`, `cpf_encrypted`, `cpf_hash`, `email` e `phone`, a gravação e leitura do CPF cifrado e a constraint de CPF único por condomínio;
  - `people/inputs.py`: `PersonInput` (Pydantic) com as validações e as mensagens pt-BR dos atributos gerais.
- Toda entidade de pessoa (proprietário agora, morador e outras depois) SHALL herdar das três bases: entidade de domínio, model e entrada. Ela acrescenta só os próprios atributos e regras. Atributos gerais e regras de proteção de dados MUST NOT ser reimplementados nas subclasses.
- A herança no ORM SHALL ser por model abstrato: cada entidade concreta tem a sua tabela com os campos herdados. Herança multi-tabela do Django MUST NOT ser usada.
- `people` é plataforma, como `tenancy`. Os apps de negócio MAY importar `people.domain`, `people.models` e `people.inputs`, o que amplia a lista de importações permitidas da ADR-0015. `people` MUST NOT importar apps de negócio.
- `people/domain.py` segue a ADR-0014: Python puro e 100% de cobertura.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Composição: Pessoa como cadastro único e proprietário/morador como papéis | Evitaria cadastros duplicados, mas o responsável preferiu manter proprietário como entidade própria que herda de Pessoa |
| Herança multi-tabela do Django (tabela `person` + tabela `owner`) | JOINs implícitos em toda consulta, e a mesma pessoa continuaria duplicada entre papéis; não traz ganho sobre o model abstrato |
| Sem base comum: cada entidade com os próprios campos e regras | Regras de CPF e proteção LGPD duplicadas e sujeitas a divergir |

## Consequências

- Mais fácil: novas entidades de pessoa ganham validação, criptografia, máscara e mensagens prontas; a proteção de dados fica num único código.
- Mais difícil: mudar um atributo geral exige migração em todas as tabelas que herdam de `PersonModel`.
- Risco aceito: a mesma pessoa física que for proprietária e moradora terá dois cadastros (um por tabela), com os dados pessoais repetidos. A unicidade de CPF vale por entidade e por condomínio, não entre entidades. Uma futura exclusão a pedido do titular (LGPD) terá de procurar o CPF em todas as tabelas de pessoa.
