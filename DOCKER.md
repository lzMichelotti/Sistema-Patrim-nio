# 🐳 Guia Completo: Docker Compose Deploy

## Visão Geral

O projeto está completamente containerizado com Docker Compose. Todos os serviços (MySQL, Backend FastAPI, Frontend React + Nginx) rodam em containers isolados com networking interno.

## Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                   Docker Compose                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Nginx      │  │   FastAPI    │  │    MySQL     │  │
│  │  (Frontend)  │  │   (Backend)  │  │   (DB)       │  │
│  │   Porta 80   │  │  Porta 8000  │  │ Porta 3306   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│       │                    │                    │       │
│       └────────────────────┴────────────────────┘       │
│             Network: app_network (bridge)              │
└─────────────────────────────────────────────────────────┘
```

## Serviços

### 1. **MySQL Database** (`db`)
- **Image:** `mysql:8.0`
- **Container Name:** `mysql_patrimonio`
- **Porta Exposta:** `3306`
- **Banco:** `patrimonio_db`
- **Usuário:** `user` / **Senha:** `password`
- **Root:** **Senha:** `rootpassword`
- **Volumes:** `mysql_data` (persistência de dados)
- **Healthcheck:** `mysqladmin ping` (retries: 5)

### 2. **Backend FastAPI** (`backend`)
- **Build:** `./backend/Dockerfile`
- **Container Name:** `patrimonio_backend`
- **Porta Interna:** `8000`
- **Porta Exposta:** `8000` (opcional, via Nginx em prod)
- **Dependência:** Aguarda MySQL saudável (`service_healthy`)
- **Variáveis de Ambiente:**
  - `DATABASE_URL=mysql+pymysql://user:password@db:3306/patrimonio_db`
  - `GOOGLE_API_KEY=${GOOGLE_API_KEY}` (carregada de `.env`)
- **Volumes:** `./backend:/app` (hot-reload em dev)
- **Network:** `app_network`

### 3. **Frontend React + Nginx** (`frontend`)
- **Build:** `./frontend/Dockerfile` (multi-stage: Node build + Nginx serve)
- **Container Name:** `patrimonio_frontend`
- **Porta Exposta:** `80`
- **Serve:** Arquivos estáticos compilados do React
- **Reverse Proxy:** `/api/*` → `http://backend:8000`
- **SPA Routing:** Redireciona URLs desconhecidas para `index.html`
- **Network:** `app_network`

## Pré-requisitos

```bash
# Verificar versões
docker --version   # Docker 20+
docker compose --version  # Docker Compose 2.0+
```

## Passo a Passo: Deploy

### 1. Clone e Navegue

```bash
git clone https://github.com/lzMichelotti/Sistema-Patrim-nio.git
cd Sistema-Patrim-nio
```

### 2. Configure Variáveis de Ambiente

```bash
# Copie o template
cp .env.docker .env

# Edite e insira sua GOOGLE_API_KEY
nano .env
# ou use seu editor favorito
```

**Arquivo `.env` esperado:**
```env
GOOGLE_API_KEY=sk-your-actual-key-here
```

### 3. Inicie os Containers

```bash
# Build e start (primeira vez, pode demorar 5-10 minutos)
docker compose up -d

# Ver status
docker compose ps
```

**Saída esperada:**
```
NAME                  STATUS          PORTS
mysql_patrimonio      Up 2 mins       0.0.0.0:3306->3306/tcp
patrimonio_backend    Up 1 min        0.0.0.0:8000->8000/tcp
patrimonio_frontend   Up 50 seconds   0.0.0.0:80->80/tcp
```

### 4. Acesse a Aplicação

- **Frontend:** http://localhost (porta 80)
- **API Docs:** http://localhost:8000/docs
- **API Base:** http://localhost/api (via Nginx reverse proxy)

## Comandos Úteis

### Monitorar Logs

```bash
# Todos os serviços
docker compose logs -f

# Serviço específico
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db
```

### Executar Comandos no Container

```bash
# Acessar shell do backend
docker compose exec backend sh

# Acessar MySQL
docker compose exec db mysql -u user -p patrimonio_db
# Senha: password

# Ver variáveis de ambiente do backend
docker compose exec backend env
```

### Parar / Remover

```bash
# Parar (preserva volumes)
docker compose down

# Parar e remover volumes (CUIDADO: deleta dados!)
docker compose down -v

# Restart
docker compose restart
```

### Rebuild (após mudanças no código)

```bash
# Rebuild sem cache
docker compose up -d --build

# Ou específico
docker compose build backend
docker compose up -d backend
```

## Variáveis de Ambiente

### Backend (Docker Compose injeta automaticamente)

| Variável | Valor | Origem |
|----------|-------|--------|
| `DATABASE_URL` | `mysql+pymysql://user:password@db:3306/patrimonio_db` | docker-compose.yml |
| `GOOGLE_API_KEY` | (carregada de `.env`) | `.env` file |

### Frontend (Buildtime)

O frontend **não recebe variáveis de ambiente em runtime** (é estático compilado). A rota `/api/*` é resolvida **no Nginx** em tempo de requisição para `http://backend:8000`.

## Troubleshooting

### "Connection refused" no Backend

**Problema:** Backend não consegue conectar ao MySQL.
**Solução:**
```bash
# Verificar se MySQL está saudável
docker compose logs db

# Aguardar healthcheck passar
docker compose ps db  # STATUS deve ser "Up X mins"

# Restart backend
docker compose restart backend
```

### Frontend não carrega API

**Problema:** Erro CORS ou 404 em `/api/*`.
**Solução:**
```bash
# Verificar nginx.conf
docker compose exec frontend cat /etc/nginx/nginx.conf

# Verificar se backend está rodando
docker compose logs backend

# Testar conexão interna
docker compose exec backend curl http://frontend/
```

### Porta 80 já em uso

**Problema:** `bind: address already in use [::]80`.
**Solução:**
```bash
# Ocupada por outro serviço
sudo lsof -i :80

# Usar porta diferente
docker compose -f docker-compose.yml -p myapp up -d
# Acessa: http://localhost:80 (ainda redireciona)
```

### Reiniciar Tudo

```bash
docker compose down -v
docker compose up -d
```

## Monitoramento em Produção

### Health Checks

```bash
# Verificar saúde dos containers
docker compose ps

# MySQL específico
docker compose exec db mysqladmin ping
```

### Logs com Filtros

```bash
# Erros do backend
docker compose logs backend | grep -i error

# Últimas 50 linhas
docker compose logs -f --tail=50 backend
```

### Estatísticas de Recursos

```bash
docker stats patrimonio_backend patrimonio_frontend mysql_patrimonio
```

## Atualizações

### Pull Novo Código

```bash
git pull origin main

# Rebuild apenas backend
docker compose build backend
docker compose up -d backend
```

### Full Rebuild

```bash
docker compose down
docker compose up -d --build
```

## Segurança em Produção

### Checklist

- [ ] `.env` **nunca** committed no Git (protegido por `.gitignore`)
- [ ] `GOOGLE_API_KEY` **nunca** exposta em logs
- [ ] MySQL com senha forte (alterar `password` em `docker-compose.yml`)
- [ ] Nginx configurado com rate limiting (opcional)
- [ ] Backups regulares de `mysql_data` volume

### Backup MySQL

```bash
docker compose exec db mysqldump -u user -p patrimonio_db > backup.sql
# Insira senha: password
```

### Restore MySQL

```bash
docker compose exec -T db mysql -u user -p patrimonio_db < backup.sql
```

## Volumes Persistentes

### Estrutura

```
Sistema-Patrim-nio/
├── docker-compose.yml
├── .env
├── .env.docker
└── docker_data/        (não aparece até containers iniciarem)
    └── mysql_data/     (dados do MySQL)
```

### Localização Física

```bash
# Linux/Mac
docker volume inspect app_network_mysql_data

# Windows (Docker Desktop)
# C:\Users\<user>\AppData\Local\Docker\volumes\app_network_mysql_data\_data\
```

## Próximos Passos

1. **Reverse Proxy (Nginx com SSL):** Configure um Nginx externo com certificado Let's Encrypt
2. **Auto-scaling:** Use Kubernetes para orquestração avançada
3. **CI/CD:** Integre GitHub Actions para deploy automático
4. **Monitoring:** Use Prometheus + Grafana para métricas
5. **Logging:** Configure ELK (Elasticsearch, Logstash, Kibana)

---

**Dúvidas?** Consulte o [README.md](README.md) ou abra uma issue no GitHub.
