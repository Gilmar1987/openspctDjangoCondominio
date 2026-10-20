# Spec Delta

## ADDED Requirements

### Requirement: Proprietário do apartamento
Um apartamento SHALL ter no máximo um proprietário, opcional, que SHALL pertencer ao mesmo condomínio. O proprietário SHALL poder ser definido, trocado ou removido na criação e na edição do apartamento (telas e API, campo `owner_id`); omitir o campo SHALL deixar o apartamento sem proprietário.

#### Scenario: Criar apartamento com proprietário
- **WHEN** o usuário cria, no condomínio C, o apartamento número "301" com o proprietário Paulo, de C
- **THEN** o apartamento é criado com Paulo como proprietário

#### Scenario: Trocar o proprietário
- **WHEN** o apartamento X pertence a Ana e o usuário edita X informando Paulo como proprietário
- **THEN** X passa a pertencer a Paulo e deixa de constar entre os apartamentos de Ana

#### Scenario: Remover o proprietário
- **WHEN** o usuário edita o apartamento X deixando o proprietário vazio
- **THEN** X fica sem proprietário

#### Scenario: Proprietário de outro condomínio ou inexistente
- **WHEN** o usuário informa, para um apartamento de C, um proprietário do condomínio D ou um identificador inexistente
- **THEN** o sistema rejeita a operação, informa em pt-BR que o proprietário não foi encontrado neste condomínio e não grava nada

#### Scenario: Opções do formulário
- **WHEN** o usuário abre o formulário de apartamento no condomínio C
- **THEN** o campo proprietário oferece "Sem proprietário" e os proprietários de C em ordem alfabética, sem exibir CPF

### Requirement: Proprietário visível nos apartamentos
A listagem de apartamentos SHALL exibir o nome do proprietário de cada unidade (ou "—" quando não houver), e a API de apartamentos SHALL retornar `owner_id` e `owner_name` (ou `null`).

#### Scenario: Listagem com e sem proprietário
- **WHEN** o condomínio C tem o apartamento "101" de Paulo e o apartamento "102" sem proprietário
- **THEN** a listagem mostra "Paulo" para o "101" e "—" para o "102"

#### Scenario: API retorna o proprietário
- **WHEN** um cliente consulta pela API o apartamento "101" de Paulo
- **THEN** a resposta inclui `owner_id` com o identificador de Paulo e `owner_name` "Paulo"
