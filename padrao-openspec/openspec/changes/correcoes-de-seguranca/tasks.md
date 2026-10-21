# Tasks

Repositório de código: `C:\openspec\tarefas`. Trabalhar na branch `fix/correcoes-de-seguranca` a partir da `main` atualizada. Comandos de verificação: seção "Comandos de verificação" do `project.md`.

## 1. Filtro de logs em tempo linear

- [ ] 1.1 Acrescentar a `tests/shared/test_logging.py` os testes de tempo de D3 (quatro piores casos de 100.000 caracteres, cada um em menos de 0,5 s) e os testes de limite (e-mail com parte local de 64 caracteres mascarado; rótulo de domínio com mais de 63 caracteres sem travar). Verificar que o teste do pior caso sem `@` falha (estoura o limite) antes da correção e que os testes de mascaramento atuais continuam passando.
- [ ] 1.2 Implementar D1 em `shared/logging.py` (padrão de e-mail limitado e aplicado só quando houver `@`). Verificar com `pytest tests/shared` passando, inclusive os testes de tempo e os de mascaramento.

## 2. Dependências sem vulnerabilidades conhecidas

- [ ] 2.1 Atualizar `requirements.txt` para `djangorestframework==3.17.2` e `pytest==9.0.3` (D4) e reconstruir a imagem. Verificar com `pip-audit -r requirements.txt` sem vulnerabilidades e com a suíte completa (`docker compose run --rm web pytest --cov --cov-config=.coveragerc`) passando, 100% nos `*/domain.py`. Se o pytest 9 exigir ajuste em testes, registrar o motivo nesta tarefa.

## 3. Auditoria no CI e documentação

- [ ] 3.1 Acrescentar o passo "Auditoria de dependências" ao `.github/workflows/ci.yml` (D5). Verificar que o YAML é válido e que o mesmo comando (`pip-audit -r requirements.txt --progress-spinner off`) termina com código 0 localmente.
- [ ] 3.2 Atualizar a linha "Auditoria de dependências" de "Comandos de verificação" no `openspec/project.md` do store (D6). Verificar que a linha traz o comando e a referência à ADR-0018.
- [ ] 3.3 Fazer commit com o trailer `OpenSpec-Change: correcoes-de-seguranca`, e o push da branch e o PR para `main` com pedido explícito do responsável. Verificar que o workflow `ci.yml` termina verde, incluindo o passo de auditoria.

## 4. ADRs

- [ ] 4.1 Revisar `openspec/adrs/0018-auditoria-de-dependencias-no-ci.md` contra o workflow implementado e promovê-la de `Proposed` para `Accepted` com aprovação explícita do responsável. Verificar que o frontmatter mostra `status: Accepted`.

## Workflow follow-up

- Após aprovação e merge do PR: `/opsx:verify` e `/opsx:archive` (sem delta specs, já que `skip_specs: true`).
