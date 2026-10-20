# Proposal

## Why

O controleCondominio ainda não tem código: não há projeto Django, ambiente local, testes nem CI. O cadastro de apartamentos é a base do domínio, já que proprietários e moradores serão vinculados a uma unidade. Por isso, esta primeira change entrega a fundação executável do projeto junto com essa primeira capability de negócio. Ela também define como o condomínio (tenant) é identificado em cada requisição, decisão que a ADR-0007 exige na primeira change.

**Resultado esperado:** com `docker compose up`, o desenvolvedor acessa telas e uma API REST para cadastrar condomínios e os apartamentos de cada condomínio. Os dados ficam isolados por condomínio, cobertos por testes Pytest que rodam no GitHub Actions.

## What Changes

- **Fundação do projeto** no repositório de código (`C:\openspec\tarefas`): projeto Django com Django REST Framework, `requirements.txt` com versões fixadas, `docker-compose` com aplicação e PostgreSQL, `.env.example`, Pytest com medição de cobertura e workflow do GitHub Actions que roda os testes unitários em cada PR.
- **Cadastro mínimo de condomínios** (tenant): criar, listar e consultar condomínios pelo nome. É o que permite endereçar o tenant na URL.
- **Identificação do tenant por segmento de URL:** todas as rotas de dados de negócio ficam sob `/condominios/<id>/...`, tanto nas telas quanto na API.
- **Cadastro de apartamentos por condomínio:** listar, criar, consultar, editar e excluir apartamentos, com os campos bloco, torre, andar e número. Haverá telas Django e endpoints REST equivalentes.
- **Isolamento por `tenant_id`:** a tabela de apartamentos tem `tenant_id`, e toda leitura e escrita é filtrada pelo condomínio da URL.

**Suposições registradas** (o usuário não detalhou estes pontos):
- O número é obrigatório. Bloco, torre e andar são opcionais.
- O andar é um inteiro: 0 para térreo e valores negativos para subsolo.
- A unicidade vale para condomínio + torre + bloco + número. Campos vazios contam como iguais entre si.
- A exclusão é definitiva (hard delete), já que ainda não existem proprietários ou moradores vinculados.

**Fora do escopo:**
- Cadastro de proprietários e moradores, e o vínculo deles com apartamentos (changes futuras).
- Editar e excluir condomínios.
- Autenticação e autorização (ADR-0005).
- Worker Celery e broker: nenhuma tarefa assíncrona é necessária agora. O serviço entra na primeira change que usar filas (ADR-0011).
- Deploy em produção e qualquer ambiente além do local (ADR-0006).
- Lint e typecheck no CI (a decisão 5.3 prevê apenas testes unitários).
- Importação em lote de apartamentos.

## Capabilities

### New Capabilities
- `condominios`: cadastro mínimo de condomínios (tenants) e identificação do condomínio da requisição pelo segmento de URL.
- `apartamentos`: cadastro das unidades de um condomínio (bloco, torre, andar, número), com unicidade e isolamento por condomínio.

### Modified Capabilities
- Nenhuma. Ainda não existem specs.

## Impact

- **Código:** cria toda a estrutura inicial do repositório `C:\openspec\tarefas`: projeto Django, fatias `condominiums` e `apartments`, templates, testes, `docker-compose.yml`, `Dockerfile`, `requirements.txt`, `.env.example` e `.github/workflows/`.
- **Dependências novas:** Django, Django REST Framework, Pydantic, psycopg, pytest, pytest-django e pytest-cov. Gunicorn não entra (só há ambiente local).
- **Superfície exposta:** novas rotas HTML e REST sob `/condominios/`, sem autenticação.
- **ADRs aplicáveis:** 0001, 0002, 0003, 0004, 0005, 0006, 0007, 0008, 0010 e 0012. A ADR-0007 é complementada pela forma de resolver o tenant definida aqui.

## Riscos

| Pergunta | Resposta |
|---|---|
| Coleta, expõe, registra em log ou retém dados pessoais ou sensíveis? | **Não aplicável.** Apartamento (bloco, torre, andar, número) e condomínio (nome) não identificam pessoas físicas. A anonimização da ADR-0009 passa a valer quando entrarem proprietários e moradores. |
| Altera autenticação, autorização ou superfície exposta? | **Sim.** Cria rotas HTML e REST sem autenticação (ADR-0005). Qualquer um com acesso à aplicação lê e altera dados de qualquer condomínio trocando o id na URL. O risco é aceito porque a aplicação só roda localmente (ADR-0006). |
| Altera esquema, volume ou padrão de acesso a dados? | **Sim.** Cria o esquema inicial: tabelas de condomínio e de apartamento, com `tenant_id`, constraint de unicidade e índice por tenant. O volume é desprezível no MVP. |
| Exige configuração, segredo ou variável de ambiente nova? | **Sim.** `SECRET_KEY` do Django, `DEBUG` e credenciais do PostgreSQL, todas em `.env` local, com `.env.example` versionado sem valores reais. O CI usa valores de teste no próprio workflow. |
| Quebra compatibilidade com clientes, integrações ou dados existentes? | **Não aplicável.** Não há código, dados nem clientes anteriores. |

## Aprovação

- Responsável: gilmar campelo
- Data: 2026-10-19
- Escopo: apply
- Condições: —
- Origem: "Eu, gilmar campelo aprovo a change cadastro-de-apartamentos para apply. Em seguida, rode /opsx:apply"
