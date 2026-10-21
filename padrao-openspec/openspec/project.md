# controleCondominio — Project Overview

> Documento preenchido pelo `/opsx:init` em 2026-10-19. O registro completo da entrevista está em [project-setup.md](project-setup.md) e as decisões duradouras em [adrs/](adrs/).

## Product Vision

O controleCondominio cadastra proprietários, seus apartamentos e moradores. O modelo é misto (B2B2C): a administração do condomínio contrata o produto, e o cadastro atende os condôminos. O MVP é pequeno (até 100 usuários ativos, até 10k req/dia), sempre conectado e em português (pt-BR).

## System Boundaries

**Dentro do escopo:**

- Cadastro de proprietários
- Cadastro de apartamentos e o vínculo entre proprietário e apartamento(s)
- Cadastro de moradores por apartamento
- Isolamento dos dados por condomínio (tenant)
- Processamento assíncrono de tarefas por fila

**Fora do escopo:**

- Autenticação e autorização (o MVP não terá autenticação; ver ADR-0005)
- Deploy em produção (nenhum ambiente além do desenvolvimento local; ver ADR-0006)
- Envio de e-mails
- Armazenamento de arquivos
- Funcionamento offline / PWA
- Internacionalização (apenas pt-BR)

## Users and Stakeholders

| Perfil | Necessidades e responsabilidades |
|---|---|
| Administração do condomínio (cliente contratante) | Contrata o produto; mantém o cadastro de proprietários, apartamentos e moradores do seu condomínio |
| Condôminos (proprietários e moradores) | Titulares dos dados pessoais cadastrados; usuários finais do cadastro |
| Desenvolvedor responsável | Mantém o código, as specs e as ADRs; aprova PRs |

## Architecture

Monólito Django organizado em **Vertical Slices**: cada feature (fatia) reúne seu handler HTTP, validação, regras e acesso a dados. As regras de negócio vivem em um **Domain Model rico** (entidades com comportamento, DDD). A interação entre módulos é feita por contratos **REST/HTTP**, sem importar internals de outra fatia. Front-end renderizado pelo próprio Django. Tarefas em background via Celery.

### Componentes e limites

| Componente | Responsabilidade | Dependências |
|---|---|---|
| Aplicação Django (fatias por feature) | Endpoints REST (DRF), páginas renderizadas pelo Django, regras de domínio | PostgreSQL, broker do Celery |
| Domínio (entidades) | Regras de negócio de proprietário, apartamento e morador | Nenhuma de infraestrutura |
| Worker Celery | Execução de tarefas assíncronas enfileiradas | Broker (Redis ou RabbitMQ — adiado: decidir na primeira change que usar filas), PostgreSQL |
| PostgreSQL | Persistência, com `tenant_id` em todas as tabelas | Contêiner Docker local |

### Fluxo de dados e integrações

Navegador → Django (páginas e endpoints REST) → validação Pydantic → entidades de domínio → Django ORM → PostgreSQL. Operações demoradas são enfileiradas para o worker Celery. Não há integrações externas no MVP.

## Domain Model

| Conceito | Responsabilidade | Regras importantes |
|---|---|---|
| Condomínio (tenant) | Delimita o isolamento dos dados | Toda tabela de negócio MUST ter `tenant_id`; toda consulta MUST filtrar por ele |
| Proprietário | Pessoa dona de um ou mais apartamentos | Dados pessoais (nome, e-mail, CPF); CPF criptografado em repouso |
| Apartamento | Unidade do condomínio | Pertence a um tenant; vinculado a proprietário(s) |
| Morador | Pessoa que reside em um apartamento | Dados pessoais protegidos pela LGPD |

## Capabilities

| Capability | Estado | Change relacionada |
|---|---|---|
| `condominios` — cadastro mínimo de condomínios (tenants) e resolução do tenant pela URL | Implementada | `2026-10-19-cadastro-de-apartamentos` |
| `apartamentos` — cadastro de unidades (torre, bloco, andar, número) por condomínio, com proprietário opcional, N moradores e exclusão bloqueada se houver moradores | Implementada | `2026-10-19-cadastro-de-apartamentos`, `2026-10-20-cadastro-de-proprietarios`, `2026-10-20-cadastro-de-moradores` |
| `proprietarios` — cadastro de proprietários (herda a base Pessoa, ADR-0016), CPF protegido, vínculo com N apartamentos e indicação de quando também é morador | Implementada | `2026-10-20-cadastro-de-proprietarios`, `2026-10-20-cadastro-de-moradores` |
| `moradores` — cadastro de moradores (herda a base Pessoa), um apartamento por morador no condomínio e reconhecimento do morador que também é proprietário (ADR-0017) | Implementada | `2026-10-20-cadastro-de-moradores` |

## Key Constraints

- **LGPD:** o produto trata dados pessoais (nome, e-mail, CPF). Dados pessoais MUST ser anonimizados em logs e relatórios; campos sensíveis (ex.: CPF) MUST ser criptografados na aplicação (ADR-0009).
- **Multi-tenant:** isolamento por coluna `tenant_id` em todas as tabelas (ADR-0007).
- **Sem autenticação no MVP** (ADR-0005) — risco aceito; ver Open Questions.
- **Sem proteção contra ataques no MVP** (sem rate limiting, WAF ou headers de segurança adicionais).
- **Volume pequeno:** até 100 usuários ativos / 10k req/dia; priorizar simplicidade.

## Stack Summary

| Área | Escolha do projeto | Observações |
|---|---|---|
| Linguagem/runtime | Python | ADR-0002 |
| Framework/plataforma | Django + Django REST Framework; front-end renderizado pelo Django | ADR-0002, ADR-0008 |
| Persistência | PostgreSQL self-hosted em contêiner; Django ORM | ADR-0003, ADR-0004 |
| Autenticação/autorização | Sem autenticação no MVP | ADR-0005 |
| Validação | Pydantic | ADR-0012 |
| Testes | Pytest; sem E2E; 100% de cobertura nos módulos de domínio (TDD estrito) | Cenários de interface com verificação em navegador versionada |
| Build/execução | pip + requirements.txt; execução via docker-compose local | ADR-0006 |
| Deploy/infraestrutura | Sem deploy em produção; apenas ambiente de desenvolvimento local; sem CDN | Secrets em `.env` local + variáveis da plataforma |
| Observabilidade | Logs em console/stdout; sem monitoramento de erros; sem tracing | — |
| Jobs/filas | Celery (broker Redis ou RabbitMQ, a decidir) | ADR-0011 |

## Comandos de verificação

Executados no repositório de código (`C:\openspec\tarefas`).

| Finalidade | Comando | Observações |
|---|---|---|
| Instalar dependências | `docker compose up -d --build` | Instala o `requirements.txt` na imagem `web`; fora do Docker: `pip install -r requirements.txt` (Python 3.12) |
| Executar localmente | `docker compose up -d` | Aplica as migrações ao subir; porta definida por `WEB_PORT` no `.env` (padrão 8000) |
| Testes | `docker compose run --rm web pytest --cov --cov-config=.coveragerc` | Exige 100% de linhas e branches em `*/domain.py`; o CI (GitHub Actions) roda o mesmo |
| Lint | Não aplicável | Decisão 5.3: o CI roda só testes unitários |
| Typecheck/build | Não aplicável | Python sem typecheck adotado |
| Migrações | `docker compose run --rm web python manage.py makemigrations --check --dry-run` | Falha se houver migração pendente; também roda no CI |
| Auditoria de dependências | `pip install pip-audit==2.10.1` e `pip-audit -r requirements.txt --progress-spinner off` | Bloqueante no CI (ADR-0018); exceção só com `--ignore-vuln <ID>` justificada no workflow |
| Varredura de secrets | Não aplicável no MVP | Adotar uma ferramenta (ex.: `gitleaks`) exige change própria; `.env` fora do git e `.env.example` sem valores reais |

## Development Conventions

- **Idioma do código:** Inglês (classes, funções, variáveis, tabelas).
- **Idioma dos textos visíveis ao usuário:** Português (pt-BR), sem i18n.
- **Organização e estilo:** Vertical Slice por feature; Domain Model rico (DDD); módulos se comunicam por REST/HTTP; monorepo (ADR-0001, ADR-0010).
- **Git e revisão:** GitHub Flow (branches de feature curtas, PR para `main`); PR exige aprovação + CI verde (GitHub Actions).
- **Testes e critérios de qualidade:** Pytest; CI roda testes unitários; 100% de cobertura nos módulos de domínio com TDD estrito; sem testes E2E — cenários de interface cobertos por verificação em navegador versionada no repositório.
- **Segurança e tratamento de dados:** anonimização de dados pessoais em logs e relatórios; criptografia de campos sensíveis (ex.: CPF) na aplicação; secrets fora do repositório (`.env` local).

## Open Questions

- **Autenticação × multi-tenant × LGPD:** sem autenticação, o sistema não identifica o usuário nem o tenant da requisição, e não há controle de acesso a dados pessoais. Rever antes de qualquer uso com dados reais (exigirá ADR que substitua a ADR-0005).
- **Broker do Celery:** Redis ou RabbitMQ — decidir na primeira change que usar filas.
- **Resolução do tenant:** como a requisição informa o `tenant_id` enquanto não houver autenticação.
- **Ambiente de produção:** não definido; a 3.4 previa PostgreSQL em contêiner também em produção.
- **Validação Pydantic com Django/DRF:** definir na primeira change como Pydantic convive com DRF Serializers e Django Forms.
