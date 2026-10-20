# Verificação em navegador: cadastro de proprietários

Roteiro dos cenários de interface das specs `proprietarios` e `apartamentos` (delta) da change `cadastro-de-proprietarios`. O projeto não tem testes E2E (decisão 5.5), então este roteiro é executado em navegador a cada mudança nas telas, e o resultado é registrado ao final.

**Pré-requisitos:**
- `docker compose up -d` com a aplicação em `http://localhost:<WEB_PORT>/` e o `.env` com `FIELD_ENCRYPTION_KEY` e `CPF_HASH_KEY`.
- Um condomínio "Aurora" e outro "Solar" cadastrados.
- **Usar só os CPFs de teste abaixo, nunca dados reais.**

## Passos

| # | Ação | Resultado esperado | Cenário da spec |
|---|---|---|---|
| 1 | Em `/condominios/`, clicar em "Proprietários" de Aurora | Página "Proprietários — Aurora" com "Nenhum proprietário cadastrado." | proprietarios: Condomínio sem proprietários |
| 2 | "Novo proprietário": nome "Maria Souza", CPF "529.982.247-26", e-mail "maria@exemplo.com" → salvar | "O CPF informado é inválido." junto ao campo CPF; nome e e-mail preservados | proprietarios: Erro de validação na página web |
| 3 | Corrigir o CPF para "529.982.247-25" e o telefone para "(81) 99999-0000" → salvar | Lista mostra Maria Souza, CPF `***.982.247-**`, telefone "(81) 99999-0000" e 0 apartamentos; "529.982.247-25" não aparece na página | proprietarios: Criação com todos os campos; CPF mascarado na listagem |
| 4 | "Novo proprietário" com nome "Outra" e CPF "52998224725" | "Já existe proprietário com este CPF neste condomínio." | proprietarios: CPF repetido no mesmo condomínio |
| 5 | Em Apartamentos de Aurora, criar torre "A" número "101", torre "A" número "102" e número "103" | Os três aparecem com Proprietário "—" | — |
| 6 | Em Proprietários, criar "Paulo", CPF "111.444.777-35", marcando A/101 e A/102 | Lista mostra Paulo com 2 apartamentos; o detalhe de Paulo lista "Torre A · Nº 101" e "Torre A · Nº 102" com o CPF mascarado | proprietarios: Vincular N apartamentos; Consulta com apartamentos vinculados |
| 7 | "Editar" Maria Souza | O campo CPF traz o CPF completo; entre os apartamentos aparece só "Nº 103" (101 e 102 são de Paulo) | proprietarios: Opções do formulário; Proteção do CPF |
| 8 | Abrir Apartamentos de Aurora | 101 e 102 com Proprietário "Paulo"; 103 com "—"; coluna Moradores com 0 (desde `cadastro-de-moradores`) | apartamentos: Listagem com e sem proprietário |
| 9 | "Editar" o apartamento 103 | O campo Proprietário oferece "Sem proprietário", "Maria Souza" e "Paulo", nessa ordem, sem CPF; escolher Maria Souza e salvar mostra "Maria Souza" na lista | apartamentos: Opções do formulário; Criar/trocar o proprietário |
| 10 | "Editar" Paulo desmarcando A/102 | A/102 passa a mostrar "—" em Apartamentos | proprietarios: Retirar apartamento do conjunto |
| 11 | "Excluir" Paulo → conferir a mensagem → "Excluir" | A confirmação diz "1 apartamento ficará sem proprietário."; Paulo some da lista e A/101 continua cadastrado com "—" | proprietarios: Confirmação de exclusão; Exclusão desvincula apartamentos |
| 12 | Abrir a URL de edição de Maria Souza trocando o id do condomínio pelo de Solar | Página 404 | proprietarios: Acesso cruzado |
| 13 | Rodar `docker compose logs web` | Nenhuma ocorrência de "Maria Souza", "529.982.247-2", "52998224725", "maria@exemplo.com" nem "99999-0000" | proprietarios: Dados pessoais fora dos logs |

## Execuções

| Data | Navegador | Executado por | Resultado |
|---|---|---|---|
| 2026-10-20 | Microsoft Edge 155.0.4283.62 (headless, automatizado por script local não versionado) | Claude Code, na implementação da change `cadastro-de-proprietarios` | Passos 1 a 13 OK |
| 2026-10-20 | Microsoft Edge 155.0.4283.62 (headless, automatizado por script local não versionado; cobertura fora da suíte) | Claude Code, na implementação da change `cadastro-de-moradores` | Passos 1 a 13 OK |
