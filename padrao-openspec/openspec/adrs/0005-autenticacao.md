---
id: ADR-0005
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0005: Sem autenticação no MVP

## Contexto

O dev decidiu que o MVP não terá autenticação. O produto, porém, é multi-tenant (ADR-0007) e trata dados pessoais sob a LGPD (ADR-0009). Sem identificar o usuário, o sistema não consegue derivar o tenant da sessão nem restringir quem acessa dados pessoais.

## Decisão

- O projeto SHALL NOT implementar autenticação nem autorização no MVP.
- Changes MUST NOT introduzir login, sessão de usuário, tokens ou provedores de identidade sem antes criar uma ADR que substitua esta.
- Enquanto esta ADR vigorar, o sistema MUST NOT ser exposto fora do ambiente de desenvolvimento local nem receber dados pessoais reais.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Sessão + cookie (auth nativa do Django) | Não escolhida pelo dev para o MVP |
| JWT Bearer | Não escolhida pelo dev para o MVP |
| OAuth2 / OpenID Connect | Não escolhida pelo dev para o MVP |
| Serviço gerenciado (Clerk, Auth0 etc.) | Não escolhida pelo dev para o MVP |
| Auth.js / NextAuth | Não se aplica a Django |

## Consequências

- Mais fácil: o MVP foca no cadastro, sem fluxos de login, recuperação de senha ou gestão de usuários.
- Mais difícil: o tenant da requisição precisa vir de outro mecanismo (ex.: subdomínio, cabeçalho ou parâmetro), que é forjável sem autenticação.
- Risco aceito: qualquer pessoa com acesso à aplicação lê e altera dados de qualquer tenant; isso é incompatível com uso real sob a LGPD. Adicionar autenticação depois exigirá revisar todas as fatias que resolvem o tenant.
- A recomendação é rever esta decisão antes de qualquer uso com dados reais; a auth nativa do Django (sessão + cookie) é a substituta de menor custo.
