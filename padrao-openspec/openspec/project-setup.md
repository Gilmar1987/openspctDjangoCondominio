# Registro de Inicialização — controleCondominio

**Responsável:** gilmar campelo
**Data:** 2026-10-19
**Comando:** /opsx:init

---

## 1. Projeto e Negócio

| Decisão | Escolha |
|---|---|
| Nome | controleCondominio |
| Visão | Cadastra proprietários, seus apartamentos e moradores |
| Público-alvo | Misto (B2B2C) — empresa contrata, usuário final usa |
| Volume esperado (MVP) | Pequeno — até 100 usuários ativos / até 10k req/dia |
| LGPD/GDPR | Sim — coleta e processa dados pessoais (nome, e-mail, CPF etc.) |
| Multi-tenant | Sim — isolamento por coluna (`tenant_id` em todas as tabelas) |
| Idiomas | Português (pt-BR) |
| Offline/PWA | Não — sempre conectado |

## 2. Arquitetura

| Decisão | Escolha |
|---|---|
| Estilo de arquitetura | Vertical Slice — organização por feature, cada fatia com seu handler |
| Organização de repositórios | Monorepo — front-end e back-end no mesmo repositório |
| Organização das regras de negócio | Domain Model rico — entidades com comportamento (DDD) |
| Comunicação entre módulos | REST/HTTP |
| Jobs / background processing | Sim — filas de tarefas assíncronas |

## 3. Stack Técnica

| Decisão | Escolha |
|---|---|
| Back-end | Python + Django (com Django REST Framework) |
| Front-end | frontend direto no django |
| Banco de dados | PostgreSQL |
| Banco — hospedagem | Self-hosted em contêiner — Docker local e em produção |
| ORM / acesso a dados | Django ORM |
| Autenticação | sem autenticação |
| Validação | Pydantic (Python) |
| Jobs / filas | Celery (com Redis ou RabbitMQ) |
| E-mail | Não aplicável |
| Armazenamento de arquivos | Não aplicável |

## 4. Infraestrutura e Deploy

| Decisão | Escolha |
|---|---|
| Ambiente de produção | não aplicar |
| Docker | Sim — Docker apenas em desenvolvimento local (docker-compose) |
| Ambientes | Development (local) |
| Secrets / variáveis de ambiente | .env local + variáveis de ambiente da plataforma |
| CDN / cache de borda | Não — sem CDN por enquanto |

## 5. Processo e Qualidade

| Decisão | Escolha |
|---|---|
| Estratégia de branches | GitHub Flow — branches de feature curtas, PR para main |
| CI/CD | Sim — GitHub Actions |
| Verificações no CI | Testes unitários |
| Testes unitários | Pytest (Python) |
| Testes E2E | Não aplicável — sem testes E2E por enquanto |
| Cobertura mínima | 100% nos módulos de domínio (TDD estrito) |
| Revisão de código | Sim — aprovação + CI verde obrigatórios |

## 6. Observabilidade e Segurança

| Decisão | Escolha |
|---|---|
| Logs | Console / stdout — coletado pela plataforma |
| Monitoramento de erros | Não — apenas logs por enquanto |
| Tracing distribuído | Não aplicável |
| Proteção contra ataques | Nenhuma no MVP |
| Controles LGPD/GDPR | Anonimização de dados em logs e relatórios |
| Dados em repouso | Criptografia de campos sensíveis na aplicação (ex.: CPF) |

## 7. Complemento da stack

| Campo | Escolha |
|---|---|
| Build/execução | pip + requirements.txt, executado via docker-compose local |
| Idioma do código | Inglês — código em inglês, textos de interface em pt-BR |

## Observações da entrevista

- A 5.1 foi respondida inicialmente como "Apenas main" e alterada para "GitHub Flow" pelo responsável, para ficar coerente com a 5.7 (aprovação + CI verde obrigatórios).
- A 3.4 registra "Docker local e em produção", mas a 4.1 não define produção e a 4.2 restringe o Docker ao desenvolvimento local; na prática, o PostgreSQL roda no docker-compose local.
- O broker do Celery (Redis ou RabbitMQ) fica para a primeira change que usar filas.

---

> Documento gerado automaticamente pelo comando `/opsx:init`.
> Para revisar as decisões, edite este arquivo e atualize `openspec/project.md` e `openspec/config.yaml`.
