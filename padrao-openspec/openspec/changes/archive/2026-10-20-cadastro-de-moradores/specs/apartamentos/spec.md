# Spec Delta

## ADDED Requirements

### Requirement: Moradores do apartamento
Um apartamento SHALL poder ter vários moradores. A listagem de apartamentos SHALL exibir a quantidade de moradores de cada unidade, e a API de apartamentos SHALL retornar `resident_count`.

#### Scenario: Listagem com quantidade de moradores
- **WHEN** o apartamento A/101 de C tem 2 moradores e A/102 nenhum
- **THEN** a listagem mostra 2 para A/101 e 0 para A/102, e a API retorna `resident_count` 2 e 0

## MODIFIED Requirements

### Requirement: Excluir apartamento
O sistema SHALL permitir excluir definitivamente um apartamento do condomínio. Na página web, a exclusão SHALL exigir confirmação explícita do usuário. Um apartamento que tenha moradores SHALL NOT ser excluído; a exclusão SHALL ser recusada até que os moradores sejam excluídos ou mudem de apartamento.

#### Scenario: Exclusão confirmada
- **WHEN** o usuário confirma a exclusão de um apartamento do condomínio C
- **THEN** o sistema remove o apartamento, que deixa de aparecer na listagem de C

#### Scenario: Exclusão de apartamento inexistente
- **WHEN** o usuário tenta excluir um identificador de apartamento que não existe em C
- **THEN** o sistema responde 404 e não altera nenhum dado

#### Scenario: Exclusão de apartamento com moradores
- **WHEN** o usuário tenta excluir o apartamento A/101, que tem 2 moradores
- **THEN** o sistema recusa a exclusão, informa em pt-BR que o apartamento tem 2 moradores e precisa ficar sem moradores antes de ser excluído (API: 400 com `{"errors": {"apartment": [...]}}`), e o apartamento e os moradores permanecem
