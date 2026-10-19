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

### .NET (multi-stage)

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app/publish .
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["dotnet", "<NomeDoProjeto>.dll"]
```

### Next.js (standalone output)

```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runtime
WORKDIR /app
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY --from=build /app/public ./public
COPY --from=build /app/.next/standalone ./
COPY --from=build /app/.next/static ./.next/static
USER appuser
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/api/health || exit 1
EXPOSE 3000
CMD ["node", "server.js"]
```

> Next.js requer `output: 'standalone'` em `next.config.ts` para o modo standalone.

## docker-compose — Estrutura padrão

```yaml
services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - NODE_ENV=development
    depends_on:
      db:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:3000/api/health"]
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
    command: ["node", "worker.js"]
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
node_modules
.next
dist
bin
obj
*.md
.env*
!.env.example
```

## Integração com OpenSpec

Ao criar tarefas de containerização em `tasks.md`, use este padrão:

```markdown
- [ ] Criar Dockerfile multi-stage para produção — verificar: `docker build -t app .` sem erro e imagem roda como non-root
- [ ] Criar docker-compose com app, banco e worker — verificar: `docker compose up` sobe todos os serviços healthy
- [ ] Adicionar .dockerignore — verificar: `docker build` não copia node_modules nem .env
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
multi-stage por stack, compose para múltiplos ambientes, secrets, redes e volumes.
