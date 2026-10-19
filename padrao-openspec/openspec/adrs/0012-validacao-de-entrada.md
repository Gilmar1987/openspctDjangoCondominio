---
id: ADR-0012
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0012: Validação de entrada com Pydantic

## Contexto

Cada fatia (ADR-0001) recebe entrada por formulários Django (ADR-0008) e endpoints DRF (ADR-0002). O dev escolheu Pydantic como padrão de validação, embora Django Forms e DRF Serializers também validem entrada.

## Decisão

- A validação de entrada das fatias SHALL usar modelos Pydantic.
- Cada fatia SHALL declarar seus modelos de entrada dentro da própria fatia.
- A primeira change que receber entrada MUST definir como Pydantic convive com DRF Serializers e Django Forms (ex.: serializer/form só como adaptador, validação em Pydantic) e registrar o padrão no design.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| DRF Serializers / Django Forms (validação nativa) | O dev escolheu Pydantic como padrão |
| Validação manual | Mais código e menos consistência |
| Zod / Valibot / FluentValidation | Fora do ecossistema Python |

## Consequências

- Mais fácil: contratos de entrada tipados e reutilizáveis nos testes de domínio e nas tarefas Celery.
- Mais difícil: Pydantic não se integra nativamente ao DRF nem aos Forms; haverá código de adaptação e risco de validação duplicada.
- Risco aceito: mensagens de erro do Pydantic precisam ser traduzidas para pt-BR na camada de apresentação.
