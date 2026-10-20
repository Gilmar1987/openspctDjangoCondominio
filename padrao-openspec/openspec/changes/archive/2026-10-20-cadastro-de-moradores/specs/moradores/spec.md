# Spec Delta

## Purpose

Mantém o cadastro dos moradores de cada condomínio e o apartamento onde cada um mora, protege os dados pessoais conforme a LGPD e reconhece o morador que também é proprietário.

## ADDED Requirements

### Requirement: Campos do morador
Um morador SHALL ter nome obrigatório (1 a 120 caracteres), CPF obrigatório e válido, e-mail opcional (formato válido) e telefone opcional (10 ou 11 dígitos com DDD), com as mesmas regras de normalização e mensagens dos proprietários, e SHALL ter um apartamento de moradia obrigatório.

#### Scenario: Criação com todos os campos
- **WHEN** o usuário cria, no condomínio C, o morador "João Lima", CPF "390.533.447-05", e-mail "joao@exemplo.com", telefone "(81) 98888-1111" e apartamento A/101 de C
- **THEN** o sistema cria o morador com o CPF "39053344705", o telefone "81988881111" e o apartamento A/101

#### Scenario: Campos obrigatórios ausentes
- **WHEN** o usuário tenta criar um morador sem nome, sem CPF ou sem apartamento
- **THEN** o sistema rejeita a operação e informa em pt-BR cada campo obrigatório ausente

#### Scenario: CPF, e-mail ou telefone inválido
- **WHEN** o usuário informa o CPF "390.533.447-06", o e-mail "joao@" ou o telefone "1234"
- **THEN** o sistema rejeita a operação e informa em pt-BR o campo inválido

### Requirement: Apartamento de moradia
O apartamento de moradia SHALL pertencer ao mesmo condomínio do morador. Um apartamento SHALL poder ter vários moradores. O morador SHALL poder morar em qualquer apartamento do condomínio, inclusive em um que não seja seu, quando também for proprietário.

#### Scenario: Vários moradores no mesmo apartamento
- **WHEN** o apartamento A/101 de C já tem o morador João e o usuário cria a moradora Maria em A/101
- **THEN** o sistema cria Maria e A/101 passa a ter 2 moradores

#### Scenario: Apartamento de outro condomínio ou inexistente
- **WHEN** o usuário informa, para um morador de C, um apartamento do condomínio D ou um identificador inexistente
- **THEN** o sistema rejeita a operação, informa em pt-BR que o apartamento não foi encontrado neste condomínio e não grava nada

#### Scenario: Mudança de apartamento
- **WHEN** o usuário edita o morador João, de A/101, informando o apartamento B/202 de C
- **THEN** João passa a morar em B/202 e deixa de constar entre os moradores de A/101

#### Scenario: Proprietário morando em apartamento que não é seu
- **WHEN** Paulo é proprietário de A/101 e A/102 e o usuário o cadastra como morador de B/305, que pertence a outro dono
- **THEN** o sistema cria o morador Paulo em B/305

### Requirement: Um único apartamento por morador no condomínio
Dentro de um condomínio, o CPF SHALL ser único entre os moradores, de modo que a mesma pessoa more em um único apartamento do condomínio, ainda que seja proprietária de vários. O mesmo CPF SHALL poder ser morador em condomínios diferentes.

#### Scenario: Mesma pessoa em outro apartamento do condomínio
- **WHEN** João (CPF "39053344705") mora em A/101 de C e o usuário tenta cadastrá-lo também como morador de B/202 de C
- **THEN** o sistema rejeita a operação e informa em pt-BR que já existe morador com este CPF neste condomínio

#### Scenario: Mesmo CPF em outro condomínio
- **WHEN** João mora em A/101 de C e o usuário cadastra o mesmo CPF como morador de um apartamento do condomínio D
- **THEN** o sistema cria o morador em D

### Requirement: Proteção dos dados pessoais do morador
O CPF do morador SHALL ser armazenado criptografado. Listagens (telas e API) SHALL exibir o CPF mascarado (`***.NNN.NNN-**`); o CPF completo SHALL aparecer apenas no formulário de edição e na consulta individual pela API. Nome, CPF, e-mail e telefone SHALL NOT aparecer em claro nos logs.

#### Scenario: CPF mascarado e ilegível no banco
- **WHEN** o morador com CPF "39053344705" é gravado e listado
- **THEN** a listagem mostra "***.533.447-**", não contém o CPF completo, e a coluna do CPF no banco não contém "39053344705"

#### Scenario: Dados pessoais fora dos logs
- **WHEN** uma criação de morador é rejeitada por validação e o sistema registra o evento em log
- **THEN** o registro não contém o nome, o CPF, o e-mail nem o telefone enviados

### Requirement: Listar e consultar moradores
O sistema SHALL listar os moradores de um condomínio em ordem alfabética de nome, com o apartamento de cada um, e SHALL permitir consultar um morador pelo identificador.

#### Scenario: Listagem ordenada com apartamento
- **WHEN** o condomínio C tem os moradores "Maria" (B/202) e "João" (A/101)
- **THEN** a listagem mostra "João — Torre A · Nº 101" antes de "Maria — Torre B · Nº 202"

#### Scenario: Condomínio sem moradores
- **WHEN** o usuário lista os moradores de um condomínio sem nenhum cadastrado
- **THEN** o sistema retorna uma lista vazia; a página web exibe "Nenhum morador cadastrado"

### Requirement: Morador que também é proprietário
O sistema SHALL reconhecer que um morador e um proprietário do mesmo condomínio são a mesma pessoa quando têm o mesmo CPF. A consulta e a listagem de moradores SHALL indicar esse vínculo e quantos apartamentos a pessoa possui. O formulário de novo morador SHALL permitir pré-preencher nome, CPF, e-mail e telefone a partir de um proprietário do condomínio, sem gravar nada até o envio.

#### Scenario: Morador reconhecido como proprietário
- **WHEN** Paulo é proprietário de A/101 e A/102 em C, com CPF "11144477735", e o usuário cadastra o morador Paulo com o mesmo CPF em C
- **THEN** a listagem e a consulta do morador indicam "também é proprietário (2 apartamentos)"

#### Scenario: Morador sem cadastro de proprietário
- **WHEN** o morador João não tem cadastro de proprietário em C
- **THEN** a listagem e a consulta não indicam vínculo de proprietário

#### Scenario: Proprietário de outro condomínio não é reconhecido
- **WHEN** o CPF do morador de C pertence a um proprietário apenas do condomínio D
- **THEN** o morador de C não é indicado como proprietário

#### Scenario: Pré-preencher a partir do proprietário
- **WHEN** o usuário abre o formulário de novo morador em C e escolhe o proprietário Paulo como base
- **THEN** o formulário vem preenchido com nome, CPF, e-mail e telefone de Paulo, e nada é gravado até o usuário escolher o apartamento e salvar

### Requirement: Editar e excluir morador
O sistema SHALL permitir editar os dados e o apartamento de um morador, com as mesmas validações da criação, e SHALL permitir excluí-lo definitivamente, com confirmação explícita na página web. Excluir um morador SHALL NOT afetar o cadastro de proprietário da mesma pessoa.

#### Scenario: Edição válida
- **WHEN** o usuário altera o telefone do morador João
- **THEN** o sistema grava o novo telefone e João continua no mesmo apartamento

#### Scenario: Exclusão confirmada
- **WHEN** o usuário confirma a exclusão do morador Paulo, que também é proprietário
- **THEN** o morador é removido, e o proprietário Paulo e os apartamentos dele continuam cadastrados

### Requirement: Isolamento e interfaces de moradores
Toda operação de morador SHALL ocorrer sob `condominios/<id>/moradores/` (páginas e `/api/...`) e ser restrita ao condomínio da URL; morador de outro condomínio SHALL ser tratado como inexistente (404). Telas em pt-BR e API JSON SHALL aplicar as mesmas validações, com os códigos 201, 200, 204, 400 e 404.

#### Scenario: Acesso cruzado
- **WHEN** o morador M pertence ao condomínio D e o usuário consulta, edita ou exclui M sob `condominios/<C>/`
- **THEN** o sistema responde 404 e M permanece inalterado

#### Scenario: Erro de validação na API e na página
- **WHEN** um cliente da API ou o formulário web envia um morador com CPF inválido
- **THEN** a API responde 400 com `{"errors": {"cpf": ["<mensagem em pt-BR>"]}}` e a página reexibe o formulário com os valores preservados e a mensagem junto ao campo CPF
