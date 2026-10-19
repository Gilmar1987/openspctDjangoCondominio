---
id: ADR-0010
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0010: Monorepo

## Contexto

Front-end (templates Django, ADR-0008), back-end, worker Celery, configuração do docker-compose e CI evoluem juntos e são mantidos por um time pequeno.

## Decisão

- Todo o código da aplicação (front-end, back-end, worker, docker-compose e workflows do GitHub Actions) SHALL ficar em um único repositório de código.
- As specs e ADRs SHALL continuar no store OpenSpec `tarefas`, declarado em `openspec/config.yaml` do repositório de código.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Multi-repo | Coordenação de versões entre repositórios sem benefício para um único deploy |
| Apenas back-end | O produto tem front-end próprio |
| Apenas front-end | O produto tem back-end próprio |

## Consequências

- Mais fácil: uma change atravessa front-end e back-end em um único PR; um só pipeline de CI.
- Mais difícil: nada relevante no tamanho atual.
- Risco aceito: specs em repositório separado (store) exigem manter as duas referências sincronizadas nas changes.
