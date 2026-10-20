---
id: ADR-0015
status: Accepted
date: 2026-10-19
supersedes: ADR-0001 (somente a regra de comunicação entre módulos por REST/HTTP)
superseded_by:
related_changes: [cadastro-de-proprietarios]
---

# ADR-0015: Comunicação entre fatias por contrato público in-process

## Contexto

A ADR-0001 manda que módulos se comuniquem por contratos REST/HTTP e proíbe uma fatia de importar internals de outra. A change `cadastro-de-proprietarios` é a primeira em que duas capabilities de negócio dependem uma da outra: `owners` precisa listar e vincular apartamentos, e `apartments` precisa listar e validar proprietários. A exclusão de um proprietário precisa ainda desvincular os apartamentos dele na mesma transação.

Todas as fatias rodam no mesmo processo Django e no mesmo banco (ADR-0001, ADR-0003). Chamar a própria API por HTTP exigiria um cliente HTTP e uma URL base configurada. Também tiraria a atomicidade: o proprietário poderia ser excluído sem que os apartamentos fossem desvinculados. A ADR-0013 já abriu um precedente com `tenancy/public.py`.

## Decisão

- Cada app de negócio que precise ser usado por outro SHALL expor um módulo `public.py` com funções e tipos simples (dataclasses, UUIDs, strings), sem models do ORM.
- Uma fatia MAY importar apenas o `public.py` de outro app. Importar `models`, `repository`, `domain`, `inputs` ou `features` de outro app MUST NOT acontecer.
- Chaves estrangeiras entre tabelas de apps diferentes são permitidas e são declaradas pelo app dono da coluna.
- Operações que atravessam apps e precisam de atomicidade SHALL rodar na mesma transação de banco, chamando o `public.py` do outro app dentro dela.
- A regra da ADR-0001 de que "a comunicação entre módulos SHALL usar REST/HTTP" fica substituída por esta. O restante da ADR-0001 (Vertical Slice, domínio rico, monólito) continua vigente.
- Um teste automatizado SHALL verificar que nenhum app importa outro fora de `public.py`.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Manter REST/HTTP in-process entre fatias | Exige cliente HTTP e URL base, adiciona latência e serialização, e perde a atomicidade da exclusão com desvinculação |
| Colocar proprietários dentro do app `apartments` | Contraria a ADR-0014 (uma capability por app) e mistura dois agregados |
| Eventos de domínio / mensageria (Celery) | Assíncrono e eventual; desproporcional para consultas síncronas de formulário |
| Liberar imports livres entre apps | Perde a fronteira entre fatias que a ADR-0001 quer preservar |

## Consequências

- Mais fácil: consultas e vínculos entre capabilities com uma chamada de função e uma transação; o contrato de cada app fica explícito num único arquivo.
- Mais difícil: cada `public.py` vira uma API interna que precisa ser mantida estável; mudanças nele afetam os apps que o usam.
- Risco aceito: o acoplamento entre apps cresce (FKs e chamadas síncronas). Separar um app em serviço próprio no futuro exigirá trocar o `public.py` por um cliente remoto.
- Ao ser aceita, a ADR-0001 MUST receber `superseded_by: ADR-0015 (regra de comunicação)`.
