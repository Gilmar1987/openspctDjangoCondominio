# Proposal

## Why

O cadastro já tem condomínios, apartamentos e proprietários, mas não sabe quem mora em cada unidade. Morador é a última capability planejada do domínio (project.md: "Cadastro de moradores — Planejada"). É também a segunda entidade de pessoa: pela ADR-0016, ela herda da base `Pessoa`, e é a primeira vez que a mesma pessoa física pode aparecer em dois cadastros, como proprietária e como moradora.

**Resultado esperado:** o usuário cadastra os moradores de cada apartamento, vários por unidade, cada morador em um único apartamento. O sistema reconhece sozinho, pelo CPF, quando um morador também é proprietário, e vice-versa, e mostra isso nas duas telas.

## What Changes

- **Cadastro de moradores por condomínio:** listar, criar, consultar, editar e excluir, em telas Django e API REST, sob `condominios/<id>/moradores/`. O morador herda de `Pessoa` os atributos e regras gerais (nome e CPF obrigatórios, e-mail e telefone opcionais, CPF cifrado e mascarado) e acrescenta o **apartamento onde mora**, obrigatório e do mesmo condomínio.
- **Um apartamento, N moradores:** um apartamento pode ter vários moradores. Um morador mora em exatamente um apartamento, e mudar de apartamento é uma edição.
- **Um único apartamento por morador no condomínio:** o CPF do morador é único entre os moradores do condomínio, então a mesma pessoa não pode morar em dois apartamentos dele.
- **Morador que também é proprietário:** os cadastros continuam separados (ADR-0016), e o sistema reconhece que são a mesma pessoa pelo hash do CPF.
  - A tela e a API do morador indicam "também é proprietário" (com quantos apartamentos), e as do proprietário indicam "também é morador" (de qual apartamento).
  - O formulário de novo morador permite **pré-preencher** os dados a partir de um proprietário do condomínio.
  - O proprietário-morador pode morar em qualquer apartamento, inclusive um que não seja dele.
- **Apartamentos:** a listagem e a API passam a mostrar a quantidade de moradores. A **exclusão de um apartamento com moradores passa a ser bloqueada**.

**Suposições registradas:**
- O CPF é obrigatório para todo morador. Dependentes sem CPF ficam fora do cadastro por ora.
- Os dados de um morador que também é proprietário **não são sincronizados**: corrigir o telefone no cadastro de proprietário não altera o de morador. É o risco aceito na ADR-0016.
- O reconhecimento é por CPF dentro do mesmo condomínio. Em condomínios diferentes, os cadastros não são relacionados.
- O pré-preenchimento a partir do proprietário copia nome, CPF, e-mail e telefone para o formulário. O usuário confirma antes de salvar.

**Fora do escopo:**
- Unificar proprietário e morador num cadastro único (seria uma revisão da ADR-0016).
- Moradores sem CPF (dependentes), tipo de vínculo (inquilino, familiar), datas de entrada e saída e histórico de moradia.
- Sincronização automática de dados entre os cadastros de proprietário e de morador da mesma pessoa.
- Autenticação (ADR-0005).

## Capabilities

### New Capabilities
- `moradores`: cadastro de moradores de um condomínio, apartamento de moradia, proteção dos dados pessoais e reconhecimento do morador que também é proprietário.

### Modified Capabilities
- `apartamentos`: o apartamento passa a mostrar a quantidade de moradores, e a exclusão de apartamento com moradores fica bloqueada (o requisito "Excluir apartamento" muda).
- `proprietarios`: o proprietário passa a indicar quando também é morador e onde mora.

## Impact

- **Código (`C:\openspec\tarefas`):**
  - novo app `residents`, com `Resident(Person)`, `ResidentRecord(PersonModel)`, `ResidentInput(PersonInput)`, `public.py`, fatias, templates e testes;
  - `apartments`: contagem de moradores na listagem e na API, e bloqueio na exclusão;
  - `owners`: indicação de "também é morador" e busca pelo hash do CPF no `public.py`;
  - migração `residents/0001` (FK para `apartment` com `PROTECT`).
- **API:** novos endpoints `/api/condominios/<id>/moradores/`. As respostas de apartamentos ganham `resident_count`, e as de proprietários ganham `resident_of`. Os campos são novos e a mudança é compatível. **Muda um comportamento:** `DELETE` de apartamento com moradores passa a responder 400.
- **Arquitetura:** a ADR-0017 (`Proposed`) define o reconhecimento da mesma pessoa entre entidades pelo hash do CPF.
- **ADRs aplicáveis:** 0001, 0005, 0007, 0009, 0012 a 0016.
- **Sem dependência nova** e sem variável de ambiente nova: reusa `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY`.

## Riscos

| Pergunta | Resposta |
|---|---|
| Coleta, expõe, registra em log ou retém dados pessoais ou sensíveis? | **Sim.** Nome, CPF, e-mail e telefone de moradores (LGPD), com a mesma proteção dos proprietários: CPF cifrado, mascarado nas listagens, completo só na edição e no GET individual, ausente dos logs. O pré-preenchimento expõe os dados do proprietário no formulário de morador, dentro do mesmo condomínio. Sem autenticação (ADR-0005), só dados de teste. |
| Altera autenticação, autorização ou superfície exposta? | **Sim, a superfície exposta.** Cria rotas HTML e REST de moradores sem autenticação. Risco aceito porque a aplicação só roda localmente (ADR-0006). |
| Altera esquema, volume ou padrão de acesso a dados? | **Sim.** Cria a tabela `resident` (com `tenant_id`, CPF cifrado com hash único por condomínio e FK para `apartment` com `PROTECT`). As listagens fazem uma consulta extra por hash de CPF para reconhecer a mesma pessoa entre cadastros. O volume é desprezível. |
| Exige configuração, segredo ou variável de ambiente nova? | **Não aplicável.** Reusa `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY`. O reconhecimento entre cadastros depende de os dois usarem a mesma `CPF_HASH_KEY`, que já é única no projeto. |
| Quebra compatibilidade com clientes, integrações ou dados existentes? | **Sim, num ponto.** `DELETE /api/condominios/<id>/apartamentos/<apt>/` de um apartamento com moradores passa de 204 para 400. Como antes desta change não existem moradores, nenhum dado atual é afetado. Os campos novos nas respostas são aditivos. |

## Aprovação

- Responsável: gilmar campelo
- Data: 2026-10-20
- Escopo: apply
- Condições: —
- Origem: "Eu, gilmar campelo, aprovo a change cadastro-de-moradores para apply e rode /opsx:apply"
- Archive: 2026-10-20; Origem: pergunta "A aprovação desta change cobre só o apply. Você confirma o arquivamento da change cadastro-de-moradores (mover para changes/archive e commitar no store; sem push)?", resposta "Sim, confirmo o arquivamento"
