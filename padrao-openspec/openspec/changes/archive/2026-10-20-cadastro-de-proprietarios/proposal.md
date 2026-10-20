# Proposal

## Why

Os apartamentos já são cadastrados por condomínio, mas o sistema ainda não sabe a quem cada unidade pertence. O cadastro de proprietários é o próximo passo do domínio (project.md: "Cadastro de proprietários — Planejada"): cada proprietário pode ter N apartamentos, e é essa relação que mais tarde vai sustentar o cadastro de moradores. É também a primeira change que trata dados pessoais (nome, CPF, e-mail, telefone), então ela coloca em prática os controles da ADR-0009.

**Resultado esperado:** dentro de um condomínio, o usuário cadastra proprietários e vincula a cada um os seus apartamentos, tanto pelo proprietário quanto pelo apartamento, pelas telas e pela API. O CPF fica criptografado no banco, e nenhum dado pessoal aparece em claro nos logs.

## What Changes

- **Cadastro de proprietários por condomínio:** listar, criar, consultar, editar e excluir, com nome e CPF obrigatórios e e-mail e telefone opcionais. Telas Django e API REST, sob `condominios/<id>/proprietarios/`.
- **CPF:** validado pelos dígitos verificadores, único por condomínio, criptografado na aplicação e exibido mascarado nas listagens.
- **Vínculo 1:N proprietário → apartamentos:** cada apartamento tem no máximo um proprietário.
  - No apartamento: novo campo opcional "proprietário" no formulário e na API, e a listagem de apartamentos passa a mostrar o proprietário.
  - No proprietário: o usuário escolhe os apartamentos dele, e a página do proprietário lista os apartamentos vinculados.
- **Exclusão de proprietário:** o proprietário é excluído e os apartamentos dele ficam sem proprietário.
- **Logs:** dados pessoais não aparecem em claro.

**Suposições registradas:**
- O formulário do proprietário só oferece apartamentos sem proprietário ou que já são dele. Pela API, enviar um apartamento de outro proprietário é recusado (400). Para trocar o dono de uma unidade, usa-se o campo "proprietário" do apartamento.
- O CPF é aceito com ou sem máscara e guardado só com os dígitos. A unicidade vale dentro do condomínio: a mesma pessoa pode ser proprietária em dois condomínios, como dois cadastros independentes.
- Na listagem e na API, o CPF aparece mascarado (`***.456.789-**`). Ele só aparece completo na tela de edição e no GET de um proprietário pela API.
- O telefone é texto de 10 ou 11 dígitos (DDD + número), aceito com ou sem máscara.

**Fora do escopo:**
- Coproprietários (N:N), histórico de propriedade e datas de aquisição.
- Moradores.
- Consentimento, exclusão a pedido do titular e portabilidade (LGPD): não foram escolhidos para o MVP (ADR-0009).
- Busca e paginação de proprietários.
- Autenticação (ADR-0005).

## Capabilities

### New Capabilities
- `proprietarios`: cadastro de proprietários de um condomínio (nome, CPF, e-mail, telefone), proteção do CPF e vínculo com os apartamentos pelo lado do proprietário.

### Modified Capabilities
- `apartamentos`: o apartamento ganha um proprietário opcional, que precisa ser do mesmo condomínio, visível na listagem e editável no formulário e na API. Os requisitos atuais não mudam, apenas recebem acréscimos.

## Impact

- **Código (`C:\openspec\tarefas`):**
  - novo pacote de plataforma `people` com a classe base `Pessoa` (atributos gerais nome, CPF, e-mail e telefone, as regras deles e o model abstrato), que `Proprietário` e as futuras entidades de pessoa herdam (ADR-0016);
  - novo app `owners` (domínio, entrada, repositório, fatias, templates e testes), com `Proprietário` herdando de `Pessoa`;
  - em `apartments`: coluna `owner_id` (FK opcional), entrada, repositório, fatias de criar/editar/listar/consultar e templates;
  - utilitário de criptografia de campo e de mascaramento em `shared/`;
  - filtro de logs;
  - migrações.
- **Dependência nova:** `cryptography` (Fernet) para a criptografia de campo.
- **Configuração nova:** `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY` no `.env`, no `.env.example` e no workflow de CI.
- **API:** novos endpoints `/api/condominios/<id>/proprietarios/`. Os endpoints de apartamentos passam a aceitar e devolver `owner_id`. A mudança é compatível: o campo é opcional e ausente equivale a "sem proprietário".
- **Arquitetura:** as fatias `owners` e `apartments` precisam consultar dados uma da outra (listas para seleção, vínculo, desvinculação na exclusão). Isso esbarra na regra da ADR-0001 de "comunicação entre módulos por REST/HTTP" e é tratado no design.
- **ADRs aplicáveis:** 0001, 0004, 0005, 0007, 0009, 0012, 0013, 0014 e 0015. A ADR-0016 (Pessoa como base herdada) é nova e está `Proposed`.

## Riscos

| Pergunta | Resposta |
|---|---|
| Coleta, expõe, registra em log ou retém dados pessoais ou sensíveis? | **Sim.** Nome, CPF, e-mail e telefone de proprietários (LGPD). O CPF é criptografado em repouso e só aparece completo na edição e no GET individual. Os dados pessoais não vão para os logs em claro (ADR-0009). Como não há autenticação (ADR-0005), o sistema MUST NOT receber dados reais: só dados de teste. |
| Altera autenticação, autorização ou superfície exposta? | **Sim, a superfície exposta.** Cria rotas HTML e REST de proprietários sem autenticação, que expõem dados pessoais a quem tiver acesso à aplicação. O risco é aceito porque a aplicação só roda localmente (ADR-0006). |
| Altera esquema, volume ou padrão de acesso a dados? | **Sim.** Cria a tabela de proprietários (com `tenant_id`, CPF criptografado e hash para unicidade) e acrescenta `owner_id` (FK opcional, `SET NULL`) em `apartment`. A migração é aditiva, e os apartamentos existentes ficam sem proprietário. |
| Exige configuração, segredo ou variável de ambiente nova? | **Sim.** `FIELD_ENCRYPTION_KEY` (Fernet) e `CPF_HASH_KEY` (HMAC). A aplicação não sobe sem elas. Ficam no `.env` local e no `.env.example`, sem valores reais, e no CI com valores de teste. Perder a chave torna os CPFs gravados ilegíveis. |
| Quebra compatibilidade com clientes, integrações ou dados existentes? | **Não.** A API de apartamentos só ganha o campo opcional `owner_id`, e os dados existentes continuam válidos. |

## Aprovação

- Responsável: gilmar campelo
- Data: 2026-10-20
- Escopo: apply
- Condições: —
- Origem: "Eu, gilmar campelo, aprovo a change cadastro-de-proprietarios para apply"
