# Tasks

Repositório de código: `C:\openspec\tarefas`. Trabalhar na branch `fix/correcoes-de-seguranca` a partir da `main` atualizada. Comandos de verificação: seção "Comandos de verificação" do `project.md`.

## 1. Filtro de logs em tempo linear

- [x] 1.1 Acrescentar a `tests/shared/test_logging.py` os testes de tempo de D3 (quatro piores casos de 100.000 caracteres, cada um em menos de 0,5 s) e os testes de limite (e-mail com parte local de 64 caracteres mascarado; rótulo de domínio com mais de 63 caracteres sem travar). Verificar que o teste do pior caso sem `@` falha (estoura o limite) antes da correção e que os testes de mascaramento atuais continuam passando.
  - Evidência: `docker compose run --rm web pytest tests/shared/test_logging.py -rf --durations=4` → 3 failed (sem-arroba 33,0 s, arroba-no-fim 31,6 s, so-digitos 50,3 s), 13 passed, incluindo todos os testes de mascaramento existentes (exit 1, esperado antes da correção)
- [x] 1.2 Implementar D1 em `shared/logging.py` (padrão de e-mail limitado e aplicado só quando houver `@`). Verificar com `pytest tests/shared` passando, inclusive os testes de tempo e os de mascaramento.
  - Evidência: `docker compose run --rm web pytest tests/shared -rf --durations=3` → 35 passed; pior caso de tempo 0,07 s (arroba-no-fim), contra 31–50 s antes (exit 0)

## 2. Dependências sem vulnerabilidades conhecidas

- [x] 2.1 Atualizar `requirements.txt` para `djangorestframework==3.17.2` e `pytest==9.0.3` (D4) e reconstruir a imagem. Verificar com `pip-audit -r requirements.txt` sem vulnerabilidades e com a suíte completa (`docker compose run --rm web pytest --cov --cov-config=.coveragerc`) passando, 100% nos `*/domain.py`. Se o pytest 9 exigir ajuste em testes, registrar o motivo nesta tarefa.
  - Evidência: `pip-audit -r requirements.txt` → No known vulnerabilities found (exit 0); `docker compose run --rm web pytest --cov --cov-config=.coveragerc` com DRF 3.17.2 e pytest 9.0.3 → 357 passed, 100% nos 5 `*/domain.py`, `makemigrations --check` sem pendências (exit 0). O pytest 9 não exigiu ajuste em testes

## 3. Auditoria no CI e documentação

- [x] 3.1 Acrescentar o passo "Auditoria de dependências" ao `.github/workflows/ci.yml` (D5). Verificar que o YAML é válido e que o mesmo comando (`pip-audit -r requirements.txt --progress-spinner off`) termina com código 0 localmente.
  - Evidência: YAML do `ci.yml` válido (`yaml.safe_load`), com o passo "Auditoria de dependências" após "Instalar dependências"; `pip-audit -r requirements.txt --progress-spinner off` local → No known vulnerabilities found (exit 0). A execução do passo no GitHub Actions fica para a 3.3
- [x] 3.2 Atualizar a linha "Auditoria de dependências" de "Comandos de verificação" no `openspec/project.md` do store (D6). Verificar que a linha traz o comando e a referência à ADR-0018.
  - Evidência: linha "Auditoria de dependências" do `project.md` (store) agora traz `pip install pip-audit==2.10.1` e `pip-audit -r requirements.txt --progress-spinner off`, com a observação "Bloqueante no CI (ADR-0018)"
- [x] 3.3 Fazer commit com o trailer `OpenSpec-Change: correcoes-de-seguranca`, e o push da branch e o PR para `main` com pedido explícito do responsável. Verificar que o workflow `ci.yml` termina verde, incluindo o passo de auditoria.
  - Evidência: commit 8fe9ebc com trailer; push e PR #5 com pedido explícito ("pode fazer o push e abrir o PR, inclusive do store"); GitHub Actions run 39649576157 → job `tests` pass (51 s): "No known vulnerabilities found" no passo de auditoria, "No changes detected", 357 passed, 100% no domínio

## 4. ADRs

- [x] 4.1 Revisar `openspec/adrs/0018-auditoria-de-dependencias-no-ci.md` contra o workflow implementado e promovê-la de `Proposed` para `Accepted` com aprovação explícita do responsável. Verificar que o frontmatter mostra `status: Accepted`.
  - Evidência: frontmatter de `openspec/adrs/0018-auditoria-de-dependencias-no-ci.md` → `status: Accepted` (commit e145036 no store, enviado para origin/openspec-store); aprovação: "pode fazer o push e abrir o PR, inclusive do store; aprovo a ADR-0018"

## Workflow follow-up

- Após aprovação e merge do PR: `/opsx:verify` e `/opsx:archive` (sem delta specs, já que `skip_specs: true`).
