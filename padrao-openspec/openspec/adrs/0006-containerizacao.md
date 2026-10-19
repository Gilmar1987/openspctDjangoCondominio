---
id: ADR-0006
status: Accepted
date: 2026-10-19
supersedes:
superseded_by:
related_changes: []
---

# ADR-0006: Docker apenas no desenvolvimento local, sem deploy em produção

## Contexto

O projeto precisa de um ambiente reproduzível com Django, PostgreSQL, worker Celery e broker. O dev definiu que não haverá deploy em produção por enquanto (4.1: "não aplicar") e que o único ambiente é o de desenvolvimento local.

## Decisão

- O ambiente de desenvolvimento SHALL ser definido em docker-compose, com os serviços aplicação Django, PostgreSQL, worker Celery e broker.
- O projeto SHALL NOT ter ambiente de produção, staging, QA ou preview no MVP. Criar qualquer um deles MUST ser precedido de nova ADR.
- Variáveis de ambiente e secrets SHALL ficar em `.env` local, fora do controle de versão; o repositório MUST trazer um `.env.example` sem valores reais.

## Alternativas consideradas

| Alternativa | Por que não foi escolhida |
|---|---|
| Docker em produção e local | Não há produção definida |
| Docker apenas em produção | Perderia a reprodutibilidade local com vários serviços |
| Sem contêiner | Instalar PostgreSQL e broker na máquina de cada dev é mais frágil |
| Kubernetes | Desproporcional ao MVP |
| Deploy em Vercel/AWS/Azure/GCP/VPS | O dev decidiu não ter produção por enquanto |

## Consequências

- Mais fácil: subir o ambiente completo com um comando; paridade entre desenvolvedores.
- Mais difícil: o CI (GitHub Actions) precisa subir PostgreSQL próprio (service container) se os testes dependerem do banco.
- Risco aceito: sem produção, não há validação de configuração, desempenho ou segurança em ambiente real. A opção "variáveis de ambiente da plataforma" (4.4) só valerá quando existir uma plataforma.
