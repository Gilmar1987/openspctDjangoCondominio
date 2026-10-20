# apartamentos Specification

## Purpose

Mantém o cadastro das unidades (apartamentos) de cada condomínio, identificadas por torre, bloco, andar e número. É a base para vincular proprietários e moradores no futuro.

## Requirements

### Requirement: Campos do apartamento
Um apartamento SHALL ter número obrigatório (texto de 1 a 10 caracteres) e, opcionalmente, torre (até 20 caracteres), bloco (até 20 caracteres) e andar (inteiro de -5 a 200, em que 0 é o térreo e valores negativos indicam subsolo). Campos de texto SHALL ser gravados sem espaços nas extremidades, e um texto em branco SHALL ser tratado como ausente.

#### Scenario: Criação com todos os campos
- **WHEN** o usuário cria, no condomínio C, um apartamento com torre "A", bloco "1", andar 3 e número "301"
- **THEN** o sistema cria o apartamento no condomínio C e o retorna com esses quatro valores

#### Scenario: Criação apenas com número
- **WHEN** o usuário cria, no condomínio C, um apartamento só com o número "12"
- **THEN** o sistema cria o apartamento com torre, bloco e andar ausentes

#### Scenario: Número ausente
- **WHEN** o usuário tenta criar um apartamento sem número ou com número só de espaços
- **THEN** o sistema rejeita a operação, informa em pt-BR que o número é obrigatório e não grava nada

#### Scenario: Andar fora do intervalo ou não inteiro
- **WHEN** o usuário informa andar 201, -6 ou "terceiro"
- **THEN** o sistema rejeita a operação e informa em pt-BR o intervalo aceito (-5 a 200)

#### Scenario: Texto acima do limite
- **WHEN** o usuário informa número com 11 caracteres ou torre com 21 caracteres
- **THEN** o sistema rejeita a operação e informa em pt-BR o limite do campo excedido

### Requirement: Unicidade do apartamento no condomínio
Dentro de um mesmo condomínio, a combinação torre + bloco + número SHALL ser única, considerando campos ausentes iguais entre si e comparando os textos sem diferenciar maiúsculas de minúsculas. O andar SHALL NOT fazer parte da unicidade.

#### Scenario: Duplicado no mesmo condomínio
- **WHEN** o condomínio C já tem o apartamento torre "A", bloco ausente, número "101", e o usuário tenta criar torre "a", bloco ausente, número "101"
- **THEN** o sistema rejeita a operação e informa em pt-BR que o apartamento já existe neste condomínio

#### Scenario: Mesmo número em torres diferentes
- **WHEN** o condomínio C já tem torre "A", número "101", e o usuário cria torre "B", número "101"
- **THEN** o sistema cria o apartamento

#### Scenario: Mesmo apartamento em outro condomínio
- **WHEN** o condomínio C já tem torre "A", número "101", e o usuário cria torre "A", número "101" no condomínio D
- **THEN** o sistema cria o apartamento no condomínio D

#### Scenario: Edição que gera duplicidade
- **WHEN** o usuário edita um apartamento do condomínio C para torre/bloco/número iguais aos de outro apartamento de C
- **THEN** o sistema rejeita a edição e mantém o apartamento inalterado

### Requirement: Listar e consultar apartamentos do condomínio
O sistema SHALL listar os apartamentos de um condomínio ordenados por torre, bloco, andar e número (ausentes primeiro) e SHALL permitir consultar um apartamento pelo seu identificador dentro do condomínio.

#### Scenario: Listagem ordenada
- **WHEN** o condomínio C tem os apartamentos torre "B" número "101" e torre "A" número "201", e o usuário lista os apartamentos de C
- **THEN** o sistema retorna torre "A" número "201" antes de torre "B" número "101"

#### Scenario: Condomínio sem apartamentos
- **WHEN** o usuário lista os apartamentos de um condomínio sem nenhum cadastrado
- **THEN** o sistema retorna uma lista vazia; a página web exibe a mensagem "Nenhum apartamento cadastrado"

### Requirement: Editar apartamento
O sistema SHALL permitir alterar torre, bloco, andar e número de um apartamento do condomínio, aplicando as mesmas validações e regras de unicidade da criação. O condomínio de um apartamento SHALL NOT poder ser alterado.

#### Scenario: Edição válida
- **WHEN** o usuário altera o andar de um apartamento do condomínio C de 3 para 4
- **THEN** o sistema grava o novo andar e retorna o apartamento atualizado

#### Scenario: Tentativa de mudar o condomínio
- **WHEN** a requisição de edição enviada à API inclui um condomínio diferente do da URL
- **THEN** o sistema ignora esse valor e o apartamento permanece no condomínio da URL

### Requirement: Excluir apartamento
O sistema SHALL permitir excluir definitivamente um apartamento do condomínio. Na página web, a exclusão SHALL exigir confirmação explícita do usuário.

#### Scenario: Exclusão confirmada
- **WHEN** o usuário confirma a exclusão de um apartamento do condomínio C
- **THEN** o sistema remove o apartamento, que deixa de aparecer na listagem de C

#### Scenario: Exclusão de apartamento inexistente
- **WHEN** o usuário tenta excluir um identificador de apartamento que não existe em C
- **THEN** o sistema responde 404 e não altera nenhum dado

### Requirement: Isolamento entre condomínios
Toda leitura, edição e exclusão de apartamento SHALL ser restrita ao condomínio da URL. Um apartamento de outro condomínio SHALL ser tratado como inexistente.

#### Scenario: Consulta cruzada
- **WHEN** o apartamento X pertence ao condomínio D e o usuário consulta X sob `/condominios/<C>/`
- **THEN** o sistema responde 404 sem revelar que X existe em outro condomínio

#### Scenario: Edição e exclusão cruzadas
- **WHEN** o usuário tenta editar ou excluir o apartamento X do condomínio D sob `/condominios/<C>/`
- **THEN** o sistema responde 404 e X permanece inalterado em D

#### Scenario: Listagem não mistura condomínios
- **WHEN** os condomínios C e D têm apartamentos e o usuário lista os apartamentos de C
- **THEN** nenhum apartamento de D aparece na listagem

### Requirement: Interface e API equivalentes para apartamentos
As operações de apartamentos SHALL estar disponíveis tanto em páginas web em pt-BR quanto em uma API REST em JSON, com as mesmas validações. A API SHALL responder 201 na criação, 200 na consulta e na edição, 204 na exclusão, 400 em erro de validação ou duplicidade e 404 em recurso inexistente.

#### Scenario: Erro de validação na API
- **WHEN** um cliente da API cria um apartamento sem número
- **THEN** a API responde 400 com um corpo JSON que indica o campo "number" e a mensagem em pt-BR

#### Scenario: Erro de validação na página web
- **WHEN** o usuário envia o formulário de apartamento sem número
- **THEN** a página é exibida de novo com os valores digitados preservados e a mensagem em pt-BR junto ao campo número
