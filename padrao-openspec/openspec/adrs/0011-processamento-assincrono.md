---
id: ADR-0011
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0011: Filas de tarefas assíncronas com Celery

## Contexto

O dev definiu que o sistema terá filas de tarefas assíncronas (2.5). A biblioteca precisa integrar-se ao Django e rodar no docker-compose local.

## Decisão

- Tarefas em background SHALL usar Celery, com worker em contêiner próprio no docker-compose.
- O broker será Redis ou RabbitMQ; a escolha MUST ser feita e registrada na primeira change que usar filas.
- Tarefas MUST ser idempotentes, MUST receber `tenant_id` explicitamente e MUST seguir a anonimização de logs (ADR-0009).
- Jobs agendados (cron) não fazem parte desta decisão.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| RQ / Dramatiq | Menos difundidos com Django; o dev escolheu Celery |
| pg-boss / BullMQ / Inngest / Trigger.dev | Ecossistema Node.js |
| Hangfire | Ecossistema .NET |

## Consequências

- Mais fácil: retries, roteamento de filas e integração madura com Django.
- Mais difícil: mais dois serviços (worker e broker) no ambiente; testes precisam de modo eager ou broker de teste.
- Risco aceito: o broker ainda indefinido pode exigir ajuste de configuração na primeira change.
