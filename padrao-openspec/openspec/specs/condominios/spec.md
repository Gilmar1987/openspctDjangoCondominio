# condominios Specification

## Purpose

Mantém o cadastro dos condomínios atendidos pelo produto. Cada condomínio é um tenant, e é ele que delimita o isolamento de todos os dados de negócio.

## Requirements

### Requirement: Criar condomínio
O sistema SHALL permitir criar um condomínio informando um nome obrigatório de 1 a 120 caracteres, sem espaços nas extremidades. Cada condomínio criado SHALL receber um identificador único gerado pelo sistema.

#### Scenario: Criação com nome válido
- **WHEN** o usuário envia a criação de um condomínio com o nome "Residencial Aurora"
- **THEN** o sistema cria o condomínio, atribui um identificador único e o retorna com o nome "Residencial Aurora"

#### Scenario: Nome ausente ou em branco
- **WHEN** o usuário envia a criação de um condomínio com nome vazio ou só com espaços
- **THEN** o sistema rejeita a criação, informa em pt-BR que o nome é obrigatório e não cria nenhum condomínio

#### Scenario: Nome acima do limite
- **WHEN** o usuário envia a criação de um condomínio com nome de 121 caracteres
- **THEN** o sistema rejeita a criação e informa em pt-BR o limite de 120 caracteres

### Requirement: Listar e consultar condomínios
O sistema SHALL listar os condomínios cadastrados em ordem alfabética de nome e SHALL permitir consultar um condomínio pelo seu identificador.

#### Scenario: Listagem ordenada
- **WHEN** existem os condomínios "Solar" e "Aurora" e o usuário solicita a listagem
- **THEN** o sistema retorna "Aurora" antes de "Solar"

#### Scenario: Consulta de condomínio inexistente
- **WHEN** o usuário consulta um identificador de condomínio que não existe
- **THEN** o sistema responde "não encontrado" (HTTP 404) sem expor detalhes internos

### Requirement: Condomínio da requisição identificado pela URL
Toda operação sobre dados de negócio SHALL ocorrer sob o segmento de caminho `condominios/<id>/` (páginas em `/condominios/<id>/...`, API em `/api/condominios/<id>/...`), e o condomínio desse segmento SHALL ser o tenant da operação. Se o identificador não existir, o sistema SHALL responder 404 sem executar a operação.

#### Scenario: Operação sob condomínio existente
- **WHEN** o usuário acessa um recurso sob `condominios/<id>/` com o identificador de um condomínio existente
- **THEN** o sistema executa a operação restrita aos dados desse condomínio

#### Scenario: Operação sob condomínio inexistente
- **WHEN** o usuário acessa um recurso sob `condominios/<id>/` com um identificador que não existe
- **THEN** o sistema responde 404 e não lê nem grava nenhum dado

### Requirement: Interface e API equivalentes para condomínios
O cadastro de condomínios SHALL estar disponível tanto em páginas web em pt-BR quanto em uma API REST com respostas em JSON, com as mesmas regras de validação nas duas.

#### Scenario: Mesma validação nas duas interfaces
- **WHEN** o usuário tenta criar um condomínio com nome vazio pela página web e depois pela API
- **THEN** as duas interfaces rejeitam a criação com a mesma mensagem em pt-BR; a API responde HTTP 400
