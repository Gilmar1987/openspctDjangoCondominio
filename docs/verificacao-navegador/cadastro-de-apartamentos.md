# Verificação em navegador: cadastro de apartamentos

Roteiro dos cenários de interface das specs `condominios` e `apartamentos` (change `cadastro-de-apartamentos`). O projeto não tem testes E2E (decisão 5.5), então este roteiro é executado em navegador a cada mudança nas telas, e o resultado é registrado ao final.

**Pré-requisito:** `docker compose up -d` com a aplicação em `http://localhost:<WEB_PORT>/`.

## Passos

| # | Ação | Resultado esperado | Cenário da spec |
|---|---|---|---|
| 1 | Abrir `/` | Redireciona para `/condominios/`, com o cabeçalho "controleCondominio" | — |
| 2 | "Novo condomínio" → salvar com nome em branco | Formulário reexibido com "O campo nome é obrigatório." | condominios: Nome ausente ou em branco |
| 3 | Criar "Residencial Aurora (roteiro)" | Volta à lista com "Condomínio … criado." e o nome listado | condominios: Criação com nome válido |
| 4 | Criar "Solar (roteiro)" | Aparece na lista em ordem alfabética | condominios: Listagem ordenada |
| 5 | Abrir "Apartamentos" de Aurora | Título com o nome do condomínio e "Nenhum apartamento cadastrado." | apartamentos: Condomínio sem apartamentos |
| 6 | "Novo apartamento": torre "Torre Norte", andar "2", número em branco → salvar | "O campo número é obrigatório." junto ao campo Número; torre e andar preservados | apartamentos: Erro de validação na página web |
| 7 | Mesmo formulário com andar "terceiro" e número "1" | "O andar deve ser um número inteiro entre -5 e 200." | apartamentos: Andar fora do intervalo ou não inteiro |
| 8 | Criar torre "A", bloco "1", andar "3", número "301" | Volta à lista com o apartamento | apartamentos: Criação com todos os campos |
| 9 | Criar torre "B", número "101"; depois torre "A", andar "2", número "201" | Lista nesta ordem: A/—/2/201, A/1/3/301, B/—/—/101 (por torre, depois bloco com ausentes primeiro); a coluna Proprietário mostra "—" nas três (desde `cadastro-de-proprietarios`) | apartamentos: Listagem ordenada |
| 10 | Criar torre "a", bloco "1", número "301" | "Este apartamento já existe neste condomínio."; nada criado | apartamentos: Duplicado no mesmo condomínio |
| 11 | "Editar" A/1/301 → andar "4" | Lista mostra andar 4 | apartamentos: Edição válida |
| 12 | "Excluir" B/101 → "Cancelar" | Página "Confirmar exclusão"; ao cancelar, o apartamento continua na lista | apartamentos: Excluir (confirmação) |
| 13 | "Excluir" B/101 → "Excluir" | Apartamento some da lista | apartamentos: Exclusão confirmada |
| 14 | Em Solar, criar torre "A", bloco "1", número "301" | Criado (mesmo apartamento em outro condomínio é permitido) | apartamentos: Mesmo apartamento em outro condomínio |
| 15 | Abrir a URL de edição do apartamento de Aurora trocando o id do condomínio pelo de Solar | Página 404 | apartamentos: Consulta cruzada |
| 16 | Abrir `/condominios/<uuid inexistente>/apartamentos/` | Página 404 | condominios: Operação sob condomínio inexistente |

## Execuções

| Data | Navegador | Executado por | Resultado |
|---|---|---|---|
| 2026-10-19 | Microsoft Edge 155.0.4283.62 (headless, automatizado por script local não versionado) | Claude Code, na implementação da change `cadastro-de-apartamentos` | Passos 1 a 16 OK |
| 2026-10-20 | Microsoft Edge 155.0.4283.62 (headless, automatizado por script local não versionado) | Claude Code, na implementação da change `cadastro-de-proprietarios` | Passos 1 a 16 OK; a coluna Proprietário ("—") do passo 9 foi conferida pelos passos 5 e 8 do roteiro de proprietários |
