# Spec Delta

## Purpose

Mantém o cadastro dos proprietários de cada condomínio e o vínculo de cada proprietário com os seus apartamentos, protegendo os dados pessoais conforme a LGPD.

## ADDED Requirements

### Requirement: Campos do proprietário
Um proprietário SHALL ter nome obrigatório (1 a 120 caracteres), CPF obrigatório, e-mail opcional (formato válido, até 254 caracteres) e telefone opcional (10 ou 11 dígitos com DDD). Textos SHALL ser gravados sem espaços nas extremidades; um texto em branco SHALL ser tratado como ausente. CPF e telefone SHALL ser aceitos com ou sem máscara.

#### Scenario: Criação com todos os campos
- **WHEN** o usuário cria, no condomínio C, o proprietário "Maria Souza", CPF "529.982.247-25", e-mail "maria@exemplo.com" e telefone "(81) 99999-0000"
- **THEN** o sistema cria o proprietário no condomínio C com o CPF "52998224725" e o telefone "81999990000"

#### Scenario: Apenas campos obrigatórios
- **WHEN** o usuário cria um proprietário só com nome e CPF válidos
- **THEN** o sistema cria o proprietário sem e-mail e sem telefone

#### Scenario: Nome ou CPF ausente
- **WHEN** o usuário tenta criar um proprietário sem nome ou sem CPF
- **THEN** o sistema rejeita a operação e informa em pt-BR cada campo obrigatório ausente

#### Scenario: E-mail ou telefone inválido
- **WHEN** o usuário informa o e-mail "maria@" ou o telefone "1234"
- **THEN** o sistema rejeita a operação e informa em pt-BR o campo inválido

### Requirement: Validação e unicidade do CPF
O CPF SHALL ter 11 dígitos com dígitos verificadores válidos, e sequências de um único dígito repetido SHALL ser rejeitadas. Dentro de um condomínio, o CPF SHALL ser único. O mesmo CPF SHALL poder existir em condomínios diferentes.

#### Scenario: CPF com dígito verificador inválido
- **WHEN** o usuário informa o CPF "529.982.247-26" ou "111.111.111-11"
- **THEN** o sistema rejeita a operação e informa em pt-BR que o CPF é inválido

#### Scenario: CPF repetido no mesmo condomínio
- **WHEN** o condomínio C já tem um proprietário com o CPF "52998224725" e o usuário cria ou edita outro proprietário de C com "529.982.247-25"
- **THEN** o sistema rejeita a operação e informa em pt-BR que já existe proprietário com este CPF neste condomínio

#### Scenario: Mesmo CPF em outro condomínio
- **WHEN** o condomínio C tem um proprietário com o CPF "52998224725" e o usuário cria um proprietário com o mesmo CPF no condomínio D
- **THEN** o sistema cria o proprietário em D

### Requirement: Proteção do CPF e dos dados pessoais
O CPF SHALL ser armazenado criptografado. Listagens (telas e API) SHALL exibir o CPF mascarado no formato `***.NNN.NNN-**`; o CPF completo SHALL aparecer apenas no formulário de edição e na consulta individual pela API. Nome, CPF, e-mail e telefone SHALL NOT aparecer em claro nos logs da aplicação.

#### Scenario: CPF mascarado na listagem
- **WHEN** o usuário lista os proprietários de um condomínio que tem o CPF "52998224725"
- **THEN** a listagem mostra "***.982.247-**" e não contém "52998224725" nem "529.982.247-25"

#### Scenario: CPF ilegível no banco
- **WHEN** um proprietário com o CPF "52998224725" é gravado
- **THEN** o valor armazenado na coluna do CPF não contém a sequência "52998224725"

#### Scenario: Dados pessoais fora dos logs
- **WHEN** uma criação de proprietário é rejeitada por validação e o sistema registra o evento em log
- **THEN** o registro não contém o nome, o CPF, o e-mail nem o telefone enviados

### Requirement: Listar e consultar proprietários do condomínio
O sistema SHALL listar os proprietários de um condomínio em ordem alfabética de nome, com a quantidade de apartamentos de cada um, e SHALL permitir consultar um proprietário pelo identificador, incluindo os apartamentos vinculados a ele.

#### Scenario: Listagem ordenada com quantidade de apartamentos
- **WHEN** o condomínio C tem os proprietários "Paulo" (2 apartamentos) e "Ana" (nenhum)
- **THEN** a listagem mostra "Ana" com 0 apartamentos antes de "Paulo" com 2

#### Scenario: Consulta com apartamentos vinculados
- **WHEN** o usuário consulta o proprietário "Paulo", dono dos apartamentos torre "A" número "101" e torre "B" número "202"
- **THEN** o sistema retorna os dados de Paulo e os dois apartamentos

#### Scenario: Condomínio sem proprietários
- **WHEN** o usuário lista os proprietários de um condomínio sem nenhum cadastrado
- **THEN** o sistema retorna uma lista vazia; a página web exibe "Nenhum proprietário cadastrado"

### Requirement: Vincular apartamentos pelo proprietário
Ao criar ou editar um proprietário, o usuário SHALL poder informar o conjunto de apartamentos dele, que substitui o conjunto anterior. Só SHALL ser aceitos apartamentos do mesmo condomínio que estejam sem proprietário ou que já pertençam a ele. Apartamentos retirados do conjunto SHALL ficar sem proprietário.

#### Scenario: Vincular N apartamentos
- **WHEN** o usuário cria o proprietário "Paulo" informando os apartamentos livres X e Y do condomínio C
- **THEN** X e Y passam a ter Paulo como proprietário

#### Scenario: Retirar apartamento do conjunto
- **WHEN** Paulo é dono de X e Y e o usuário edita Paulo informando só X
- **THEN** X continua com Paulo e Y fica sem proprietário

#### Scenario: Apartamento de outro proprietário
- **WHEN** o apartamento Z pertence a "Ana" e o usuário tenta vincular Z a Paulo pelo cadastro de Paulo
- **THEN** o sistema rejeita a operação, informa em pt-BR que o apartamento já tem outro proprietário, e Z continua com Ana

#### Scenario: Apartamento de outro condomínio ou inexistente
- **WHEN** o usuário informa, para um proprietário de C, um apartamento do condomínio D ou um identificador inexistente
- **THEN** o sistema rejeita a operação e informa em pt-BR que o apartamento não foi encontrado neste condomínio

#### Scenario: Opções do formulário
- **WHEN** o usuário abre o formulário de edição de Paulo no condomínio C
- **THEN** a seleção de apartamentos oferece só os apartamentos de C sem proprietário e os de Paulo

### Requirement: Editar e excluir proprietário
O sistema SHALL permitir editar os dados de um proprietário com as mesmas validações da criação e SHALL permitir excluí-lo definitivamente; na exclusão, os apartamentos dele SHALL ficar sem proprietário. Na página web, a exclusão SHALL exigir confirmação explícita e informar quantos apartamentos serão desvinculados.

#### Scenario: Edição válida
- **WHEN** o usuário altera o telefone de Paulo
- **THEN** o sistema grava o novo telefone e mantém os apartamentos vinculados

#### Scenario: Exclusão desvincula apartamentos
- **WHEN** o usuário confirma a exclusão de Paulo, dono de X e Y
- **THEN** Paulo é removido, X e Y continuam cadastrados e ficam sem proprietário

#### Scenario: Confirmação de exclusão
- **WHEN** o usuário abre a exclusão de Paulo na página web
- **THEN** a página pede confirmação e informa que 2 apartamentos ficarão sem proprietário, sem excluir nada antes do envio

### Requirement: Isolamento e interfaces de proprietários
Toda operação de proprietário SHALL ocorrer sob `condominios/<id>/proprietarios/` (páginas e `/api/...`) e ser restrita ao condomínio da URL; proprietário de outro condomínio SHALL ser tratado como inexistente (404). As telas em pt-BR e a API JSON SHALL aplicar as mesmas validações; a API SHALL responder 201, 200, 204, 400 e 404 como nos apartamentos.

#### Scenario: Acesso cruzado
- **WHEN** o proprietário P pertence ao condomínio D e o usuário consulta, edita ou exclui P sob `condominios/<C>/`
- **THEN** o sistema responde 404 e P permanece inalterado

#### Scenario: Erro de validação na API
- **WHEN** um cliente da API cria um proprietário com CPF inválido
- **THEN** a API responde 400 com `{"errors": {"cpf": ["<mensagem em pt-BR>"]}}`

#### Scenario: Erro de validação na página web
- **WHEN** o usuário envia o formulário de proprietário com CPF inválido
- **THEN** a página é exibida de novo com os valores preservados e a mensagem junto ao campo CPF
