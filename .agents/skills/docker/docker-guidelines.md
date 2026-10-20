# Docker Guidelines

Referência de containerização para qualquer stack. Os valores concretos (imagens,
comandos de build e de execução, porta) saem da Stack Summary e dos Comandos de
verificação do `openspec/project.md`.

---

## Dockerfile

### Multi-stage com migrações na inicialização

Quando o projeto aplica migrações ao subir o contêiner, use um script de entrada que
migra e depois substitui o processo pelo servidor:

```dockerfile
FROM <imagem-de-build> AS build
WORKDIR /src
COPY <manifestos-de-dependência> ./
RUN <comando de instalação das dependências>
COPY . .
RUN <comando de build ou empacotamento>

FROM <imagem-de-runtime> AS runtime
WORKDIR /app
RUN <criação de um usuário não-root>
COPY --from=build <artefato-gerado> .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh
USER appuser
EXPOSE <porta>
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3   CMD <checagem do endpoint de saúde> || exit 1
ENTRYPOINT ["./entrypoint.sh"]
```

`entrypoint.sh`:

```bash
#!/bin/sh
set -e
<comando de migração dos Comandos de verificação>
exec <comando de entrada em produção>
```

Em produção com várias réplicas, prefira rodar a migração como uma etapa separada do
deploy, para que duas réplicas não migrem ao mesmo tempo.

---

## docker-compose

### Ambiente de desenvolvimento — aplicação + PostgreSQL (+ worker opcional)

```yaml
services:
  app:
    build:
      context: .
      target: build
    command: <comando de execução local dos Comandos de verificação>
    ports:
      - "${APP_PORT:-8000}:<porta>"
    volumes:
      - .:/src
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy

  # Só quando o projeto tiver processamento em background (ADR de jobs/filas).
  worker:
    build:
      context: .
      target: build
    command: <comando do worker>
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:17-alpine
    ports:
      - "${DB_PORT:-5432}:5432"
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

Ao montar o código como volume (`.:/src`), exclua do volume as pastas de dependências
instaladas dentro do contêiner, com um volume anônimo por pasta (por exemplo,
`- /src/node_modules` ou `- /src/.venv`).

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

# Dependências (reconstruídas no build): mantenha só as da stack do projeto
node_modules
.venv
venv
vendor

# Build outputs e caches
dist
build
out
bin
obj
target
publish
__pycache__
*.pyc

# Ambiente e secrets
.env
.env.*
!.env.example

# Testes e cobertura
coverage
htmlcov
.coverage
.pytest_cache
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

# Aplicação
APP_PORT=8000
APP_SECRET_KEY=troque-por-um-valor-gerado-localmente

# Integrações (uma linha por chave, sem valor real)
EMAIL_API_KEY=

# Feature flags
FEATURE_X_ENABLED=false
```

---

## Boas práticas

### Segurança

- Nunca usar `root` em runtime — sempre declarar `USER` não-root
- Nunca copiar `.env` para dentro da imagem — usar variáveis de ambiente em runtime
- Usar `docker secret` ou variáveis injetadas pelo orquestrador em produção
- Escanear imagens com `docker scout cves <imagem>` antes de publicar

### Performance de build

- Copiar os manifestos de dependência (por exemplo, `package.json`, `requirements.txt`, `*.csproj`, `go.mod`) antes do código-fonte para aproveitar o cache de camadas
- Usar `--no-cache` apenas em CI; em desenvolvimento o cache acelera o ciclo
- Instalar dependências a partir do lockfile em builds reproduzíveis (por exemplo, `npm ci`, `pip install -r requirements.txt` com versões fixadas, `dotnet restore --locked-mode`)

### Health check

- Todo serviço de longa duração deve ter `HEALTHCHECK`
- Expor um endpoint de saúde (por exemplo, `/health`) que retorne 200 quando o serviço estiver pronto
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
