# Docker Guidelines

Referência completa de containerização para projetos .NET e Next.js.

---

## Dockerfile

### .NET 8 / 9 — Web API ou Minimal API

```dockerfile
# Build
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY ["src/MeuProjeto.Api/MeuProjeto.Api.csproj", "src/MeuProjeto.Api/"]
RUN dotnet restore "src/MeuProjeto.Api/MeuProjeto.Api.csproj"
COPY . .
WORKDIR "/src/src/MeuProjeto.Api"
RUN dotnet publish -c Release -o /app/publish --no-restore

# Runtime
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
COPY --from=build /app/publish .
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["dotnet", "MeuProjeto.Api.dll"]
```

### .NET 8 / 9 — com migrations automáticas

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser /app
COPY --from=build /app/publish .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s CMD curl -f http://localhost:8080/health || exit 1
ENTRYPOINT ["./entrypoint.sh"]
```

`entrypoint.sh`:

```bash
#!/bin/sh
dotnet MeuProjeto.Api.dll migrate
exec dotnet MeuProjeto.Api.dll
```

### Next.js 15 — App Router (standalone)

Requer em `next.config.ts`:

```ts
const nextConfig = {
  output: 'standalone',
}
export default nextConfig
```

```dockerfile
# Dependências
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# Build
FROM node:20-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Runtime
FROM node:20-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
COPY --from=build /app/public ./public
COPY --from=build --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=build --chown=appuser:appgroup /app/.next/static ./.next/static
USER appuser
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=5s CMD wget -qO- http://localhost:3000/api/health || exit 1
CMD ["node", "server.js"]
```

---

## docker-compose

### Ambiente de desenvolvimento — Next.js + PostgreSQL + pg-boss worker

```yaml
services:
  app:
    build:
      context: .
      target: build
    command: npm run dev
    ports:
      - "3000:3000"
    volumes:
      - .:/app
      - /app/node_modules
      - /app/.next
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=http://localhost:3000
    depends_on:
      db:
        condition: service_healthy

  worker:
    build:
      context: .
      target: build
    command: npm run worker
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Ambiente de desenvolvimento — .NET + PostgreSQL

```yaml
services:
  api:
    build:
      context: .
      target: build
    ports:
      - "8080:8080"
    environment:
      - ConnectionStrings__Default=Host=db;Database=${POSTGRES_DB};Username=${POSTGRES_USER};Password=${POSTGRES_PASSWORD}
      - ASPNETCORE_ENVIRONMENT=Development
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

### Produção — múltiplos ambientes com override

Estrutura recomendada:

```text
docker-compose.yml           # base (serviços e volumes)
docker-compose.dev.yml       # overrides de desenvolvimento (volumes, hot reload)
docker-compose.prod.yml      # overrides de produção (restart policy, limites)
```

Uso:

```bash
# Desenvolvimento
docker compose -f docker-compose.yml -f docker-compose.dev.yml up

# Produção
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

`docker-compose.prod.yml`:

```yaml
services:
  app:
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

---

## .dockerignore

```text
# Controle de versão
.git
.gitignore

# Dependências (reconstruídas no build)
node_modules
.pnp
.pnp.js

# Build outputs
.next
out
dist
build
bin
obj
publish

# Ambiente e secrets
.env
.env.*
!.env.example

# Testes e cobertura
coverage
.nyc_output
TestResults

# IDE e OS
.vscode
.idea
*.suo
*.user
.DS_Store
Thumbs.db

# Docs e assets desnecessários
*.md
!README.md
docs
```

---

## .env.example

Sempre versionar um `.env.example` com as variáveis necessárias sem valores reais:

```env
# Banco de dados
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=dbname

# Autenticação
NEXTAUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000

# E-mail
RESEND_API_KEY=re_xxxxxxxxxxxx

# Feature flags
WHATSAPP_ENABLED=false
```

---

## Boas práticas

### Segurança

- Nunca usar `root` em runtime — sempre declarar `USER` não-root
- Nunca copiar `.env` para dentro da imagem — usar variáveis de ambiente em runtime
- Usar `docker secret` ou variáveis injetadas pelo orquestrador em produção
- Escanear imagens com `docker scout cves <imagem>` antes de publicar

### Performance de build

- Copiar arquivos de dependência (`package.json`, `*.csproj`) antes do código-fonte para aproveitar cache de camadas
- Usar `--no-cache` apenas em CI; em desenvolvimento o cache acelera o ciclo
- Preferir `npm ci` a `npm install` em builds reproduzíveis

### Health check

- Todo serviço de longa duração deve ter `HEALTHCHECK`
- Expor um endpoint `/health` ou `/api/health` que retorne 200 quando o serviço estiver pronto
- Usar `--start-period` para dar tempo ao serviço inicializar antes das verificações

### Redes

- Serviços no mesmo `docker-compose.yml` se comunicam pelo nome do serviço (ex: `db`, `app`)
- Isolar serviços em redes separadas quando necessário:

```yaml
networks:
  frontend:
  backend:

services:
  app:
    networks:
      - frontend
      - backend
  db:
    networks:
      - backend
```

---

## Comandos úteis

```bash
# Build sem cache
docker build --no-cache -t meu-app .

# Inspecionar usuário do container em execução
docker inspect <container_id> --format '{{.Config.User}}'

# Ver camadas e comandos da imagem
docker history meu-app

# Verificar variáveis de ambiente do container
docker exec <container_id> env

# Logs em tempo real
docker compose logs -f app

# Remover volumes e containers parados
docker compose down -v

# Escanear vulnerabilidades
docker scout cves meu-app
```
