---
name: docker
description: >
  Use quando o usuário precisar containerizar uma aplicação, criar ou revisar
  Dockerfile, docker-compose ou configuração de ambiente Docker. Também use
  quando uma tarefa OpenSpec envolver build de imagem, deploy em container ou
  ambiente local com Docker.
license: MIT
metadata:
  author: PadraoOpenspct
  version: "1.0"
---

# Docker

Skill de containerização para projetos spec-driven. Cobre Dockerfile, docker-compose
e boas práticas de ambiente, integrada ao fluxo OpenSpec.

## Quando usar

- Criar ou revisar Dockerfile de uma aplicação
- Criar ou revisar docker-compose para ambiente local ou produção
- Containerizar uma nova capability durante `/opsx:apply`
- Revisar configuração de container antes de `/opsx:archive`

## Princípios

- Imagens mínimas: prefira `alpine` ou `distroless` como base final
- Multi-stage build obrigatório: separar build de runtime
- Nunca rodar como `root` em produção: usar `USER` não-root
- Secrets via variáveis de ambiente, nunca copiados na imagem
- Health check declarado em todo serviço de longa duração
- `.dockerignore` sempre presente para excluir `node_modules`, `.git`, artefatos de build

## Dockerfile — Estrutura padrão

O esqueleto vale para qualquer stack. Antes de escrever, leia a Stack Summary e os
Comandos de verificação do `openspec/project.md`: a imagem base, o comando de build e o
comando de entrada saem de lá.

```dockerfile
# Estágio de build: imagem com o SDK ou toolchain da linguagem
FROM <imagem-de-build> AS build
WORKDIR /src
# Copie primeiro só os manifestos de dependência, para aproveitar o cache de camadas
COPY <manifestos-de-dependência> ./
RUN <comando de instalação das dependências>
COPY . .
RUN <comando de build ou empacotamento>

# Estágio de runtime: imagem mínima, só com o necessário para executar
FROM <imagem-de-runtime> AS runtime
WORKDIR /app
COPY --from=build <artefato-gerado> .
RUN <criação de um usuário não-root, conforme a imagem>
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD <checagem do endpoint de saúde> || exit 1
EXPOSE <porta>
CMD [<comando de entrada>]
```

### O que preencher por stack

| Marcador | Como decidir |
|---|---|
| `<imagem-de-build>` | Imagem oficial do SDK ou da linguagem, na versão registrada na Stack Summary |
| `<manifestos-de-dependência>` | Os arquivos de lock e de dependências do projeto (por exemplo, `package-lock.json`, `requirements.txt`, `*.csproj`, `go.sum`) |
| `<comando de build ou empacotamento>` | O comando de typecheck/build dos Comandos de verificação, ou o empacotamento da stack |
| `<imagem-de-runtime>` | Imagem de runtime oficial, `-slim`, `alpine` ou `distroless`; para linguagens interpretadas, a mesma base enxuta da linguagem |
| `<comando de entrada>` | O comando de execução em produção (servidor de aplicação), nunca o servidor de desenvolvimento |

Se a stack não separar build e runtime (por exemplo, uma linguagem interpretada sem
etapa de compilação), mantenha os dois estágios só quando o de build instalar
ferramentas que não devem ir para a imagem final; caso contrário, use um estágio e
registre o motivo no `design.md`.

## docker-compose — Estrutura padrão

```yaml
services:
  app:
    build: .
    ports:
      - "${APP_PORT:-8000}:<porta>"
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "<checagem do endpoint de saúde>"]
      interval: 30s
      timeout: 5s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  worker:
    build: .
    command: [<comando do worker>]
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres_data:
```

## .dockerignore padrão

```text
.git
.gitignore
.env*
!.env.example
*.md
# Acrescente as pastas de dependências e de build da stack, por exemplo:
# node_modules, dist, build, .venv, __pycache__, bin, obj, target, vendor
```

Use uma porta configurável (`APP_PORT` no exemplo): se a porta padrão já estiver em uso
na máquina, o desenvolvedor troca no `.env` sem editar o compose.

## Integração com OpenSpec

Ao criar tarefas de containerização em `tasks.md`, use este padrão:

```markdown
- [ ] Criar Dockerfile multi-stage para produção — verificar: `docker build -t app .` sem erro e imagem roda como non-root
- [ ] Criar docker-compose com app, banco e worker — verificar: `docker compose up` sobe todos os serviços healthy
- [ ] Adicionar .dockerignore — verificar: `docker build` não copia dependências locais nem .env
- [ ] Configurar health check no serviço app — verificar: `docker inspect` mostra status healthy após startup
```

## Checklist antes de arquivar uma change com Docker

- [ ] Imagem builda sem erro em ambiente limpo (`docker build --no-cache`)
- [ ] Container roda como usuário não-root (`docker inspect` → `User` não vazio)
- [ ] Nenhum secret hardcoded na imagem (`docker history` não expõe credenciais)
- [ ] Health check responde dentro do timeout configurado
- [ ] `.dockerignore` exclui artefatos de build e arquivos sensíveis
- [ ] Variáveis de ambiente documentadas em `.env.example`

## Referência completa

Veja [docker-guidelines.md](docker-guidelines.md) para exemplos avançados:
migrações na inicialização, compose para múltiplos ambientes, secrets, redes e volumes.
