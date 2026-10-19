---
id: ADR-0008
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0008: Front-end renderizado pelo próprio Django

## Contexto

O produto precisa de telas de cadastro simples, em pt-BR, sempre conectadas e sem requisitos de PWA. O back-end já é Django (ADR-0002).

## Decisão

- O front-end SHALL ser renderizado pelo próprio Django (templates e views do Django), no mesmo projeto e deploy.
- Changes MUST NOT introduzir um framework SPA separado (React, Vue, Angular etc.) sem nova ADR.
- Textos visíveis ao usuário SHALL ser em pt-BR, sem infraestrutura de i18n.
- Cenários de interface SHALL ser cobertos por verificação em navegador versionada no repositório, já que o projeto não terá testes E2E.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Next.js | Exigiria um segundo runtime (Node.js) e um deploy separado |
| React puro (Vite) | SPA separada, com API e build próprios |
| Vue.js | Mesmo motivo do React |
| Angular | Peso desproporcional ao MVP |
| Blazor | Fora do ecossistema Python |

## Consequências

- Mais fácil: uma só linguagem e um só deploy; formulários, CSRF e mensagens nativos do Django.
- Mais difícil: interações ricas no cliente exigem JavaScript adicional ou bibliotecas leves; cada uma MUST ser justificada no design.
- Risco aceito: a convivência entre views de template e endpoints DRF precisa de convenção clara por fatia.
