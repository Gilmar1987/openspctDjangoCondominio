---
id: ADR-0018
status: Proposed
date: 2026-10-20
supersedes:
superseded_by:
related_changes: [correcoes-de-seguranca]
---

# ADR-0018: Auditoria de dependências bloqueante no CI

## Contexto

A decisão 5.3 do `project-setup.md` definiu que o CI roda só os testes unitários, e o `project.md` registrou "Auditoria de dependências: Não aplicável no MVP". Uma revisão de segurança feita em 2026-10-20 encontrou, com `pip-audit`, três vulnerabilidades conhecidas nas versões fixadas (`djangorestframework 3.16.1` e `pytest 8.4.2`). Nada no fluxo teria detectado isso, porque as versões fixadas (ADR-0002) não mudam sozinhas, mas novas vulnerabilidades são publicadas sobre elas.

## Decisão

- O CI SHALL rodar `pip-audit -r requirements.txt` em todo PR e em todo push para `main`, com a versão do `pip-audit` fixada no workflow.
- Uma vulnerabilidade conhecida em qualquer dependência do `requirements.txt` SHALL falhar o job.
- Uma exceção só MAY ser feita com `--ignore-vuln <ID>` no próprio workflow, acompanhada de um comentário com o motivo (por exemplo, não há versão corrigida) e uma data de revisão.
- A seção "Comandos de verificação" do `project.md` SHALL trazer o mesmo comando, para que apply e verify o executem como evidência.
- Esta decisão acrescenta uma checagem à decisão 5.3 e não substitui os testes unitários.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Manter "não aplicável no MVP" | A revisão mostrou que vulnerabilidades reais passariam despercebidas |
| Dependabot ou Renovate (PRs automáticos de versão) | Útil como complemento, mas não bloqueia um PR que introduza uma versão vulnerável; pode vir em change futura |
| Auditoria só como aviso (sem falhar o CI) | Avisos tendem a ser ignorados; o projeto exige CI verde para merge (decisão 5.7) |
| `safety` em vez de `pip-audit` | A base gratuita é mais limitada; o `pip-audit` usa a base PyPA/OSV e é mantido pela PyPA |

## Consequências

- Mais fácil: vulnerabilidades novas aparecem no próximo PR ou push, sem depender de revisão manual.
- Mais difícil: um PR sem relação com dependências pode falhar porque saiu uma vulnerabilidade nova. Nesse caso é preciso atualizar a dependência ou registrar a exceção.
- Risco aceito: a auditoria depende de rede no CI e da base de vulnerabilidades. Uma indisponibilidade dessas falha o job e exige rodar de novo.
