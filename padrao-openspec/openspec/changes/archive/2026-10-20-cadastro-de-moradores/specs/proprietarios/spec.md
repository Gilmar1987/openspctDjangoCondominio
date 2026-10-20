# Spec Delta

## ADDED Requirements

### Requirement: Proprietário que também é morador
O sistema SHALL reconhecer que um proprietário e um morador do mesmo condomínio são a mesma pessoa quando têm o mesmo CPF. A listagem e a consulta de proprietários (telas e API, campo `resident_of`) SHALL indicar o apartamento onde o proprietário mora, quando ele também for morador.

#### Scenario: Proprietário que mora em um dos seus apartamentos
- **WHEN** Paulo é proprietário de A/101 e A/102 e também é morador de A/101 em C
- **THEN** a listagem e a consulta de Paulo indicam "também é morador de Torre A · Nº 101", e a API retorna `resident_of` com esse apartamento

#### Scenario: Proprietário que não é morador
- **WHEN** a proprietária Ana não tem cadastro de morador em C
- **THEN** a listagem e a consulta não indicam moradia, e a API retorna `resident_of` nulo
