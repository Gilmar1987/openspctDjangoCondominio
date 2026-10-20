# Verificação em navegador: cadastro de moradores

Roteiro dos cenários de interface das specs `moradores`, `apartamentos` (delta) e `proprietarios` (delta) da change `cadastro-de-moradores`. O projeto não tem testes E2E (decisão 5.5), então este roteiro é executado em navegador a cada mudança nas telas, e o resultado é registrado ao final. Uma execução automatizada por script fora do repositório conta como **cobertura fora da suíte**.

**Pré-requisitos:**
- `docker compose up -d` com a aplicação em `http://localhost:<WEB_PORT>/`.
- Os condomínios "Aurora" e "Solar". Em Aurora: os apartamentos A/101 e A/102, do proprietário Paulo (CPF "111.444.777-35"), e B/202, sem proprietário.
- **Usar só os CPFs de teste deste roteiro.**

## Passos

| # | Ação | Resultado esperado | Cenário da spec |
|---|---|---|---|
| 1 | Em `/condominios/`, clicar em "Moradores" de Aurora | "Moradores — Aurora" com "Nenhum morador cadastrado." | moradores: Condomínio sem moradores |
| 2 | "Novo morador": nome "João Lima", CPF "390.533.447-06", apartamento A/101 → salvar | "O CPF informado é inválido." junto ao CPF; nome e apartamento preservados | moradores: Erro de validação na página |
| 3 | Corrigir o CPF para "390.533.447-05" → salvar | Lista mostra João Lima, `***.533.447-**`, "Torre A · Nº 101" e "—" em Proprietário? | moradores: Criação; Listagem ordenada com apartamento |
| 4 | "Novo morador" com nome "Maria", CPF "529.982.247-25", apartamento A/101 | Criada; A/101 passa a ter 2 moradores na coluna "Moradores" da lista de apartamentos | moradores: Vários moradores no mesmo apartamento; apartamentos: Listagem com quantidade de moradores |
| 5 | "Novo morador" com CPF "39053344705" e apartamento B/202 | "Já existe morador com este CPF neste condomínio." | moradores: Mesma pessoa em outro apartamento do condomínio |
| 6 | "Novo morador": escolher Paulo em "Preencher a partir do proprietário" → "Preencher" | Nome, CPF, e-mail e telefone de Paulo aparecem no formulário; a lista de moradores continua com 2 | moradores: Pré-preencher a partir do proprietário |
| 7 | Escolher o apartamento B/202 (que não é de Paulo) e salvar | Paulo é criado em B/202 com "também é proprietário (2 apartamentos)" | moradores: Proprietário morando em apartamento que não é seu; Morador reconhecido como proprietário |
| 8 | Abrir Proprietários de Aurora | Paulo aparece com "também é morador de Torre B · Nº 202"; o detalhe de Paulo mostra o mesmo em "Mora em" | proprietarios: Proprietário que também é morador |
| 9 | "Editar" João, mudar o apartamento para B/202 | João passa a "Torre B · Nº 202"; o formulário mostrava o CPF completo | moradores: Mudança de apartamento |
| 10 | Em Apartamentos, "Excluir" B/202 | A página avisa "Este apartamento tem 2 moradores e precisa ficar sem moradores antes de ser excluído." e não mostra o botão Excluir | apartamentos: Exclusão de apartamento com moradores |
| 11 | Em Moradores, "Excluir" Paulo → confirmar | Paulo some dos moradores; continua em Proprietários, sem a indicação "também é morador" | moradores: Exclusão confirmada |
| 12 | Abrir a URL de edição de João trocando o id do condomínio pelo de Solar | Página 404 | moradores: Acesso cruzado |
| 13 | Rodar `docker compose logs web` | Nenhuma ocorrência de "João Lima", "390.533.447-0", "39053344705" nem de e-mail ou telefone de teste | moradores: Dados pessoais fora dos logs |

## Execuções

| Data | Navegador | Executado por | Resultado |
|---|---|---|---|
| 2026-10-20 | Microsoft Edge 155.0.4283.62 (headless, automatizado por script local não versionado; cobertura fora da suíte) | Claude Code, na implementação da change `cadastro-de-moradores` | Passos 1 a 13 OK |
