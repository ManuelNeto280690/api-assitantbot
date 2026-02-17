# 🚀 Resumo Rápido: Deploy no Easypanel

## Passos Principais

### 1. Criar Projeto no Easypanel
- Login no Easypanel
- Create Project → `api-assitantbot`

### 2. Conectar GitHub
- Create Service → App → GitHub
- Autorizar Easypanel
- Selecionar repositório `api-assitantbot`

### 3. Criar 5 Serviços

#### Redis
- Database → Redis 7-alpine
- Nome: `redis`

#### API
- App → GitHub → `api-assitantbot`
- Branch: `main`
- **Auto Deploy: ✅ ATIVAR**
- Port: `8000`
- Command: `gunicorn app.main:app -c gunicorn.conf.py`
- Adicionar variáveis de ambiente (ver EASYPANEL-DEPLOY.md)

#### Worker
- App → GitHub → `api-assitantbot`
- **Auto Deploy: ✅ ATIVAR**
- Command: `celery -A app.workers.celery_app worker --loglevel=info`
- Mesmas variáveis do API

#### Beat
- App → GitHub → `api-assitantbot`
- **Auto Deploy: ✅ ATIVAR**
- Command: `celery -A app.workers.celery_app beat --loglevel=info`
- Mesmas variáveis do API

#### Flower (Opcional)
- App → GitHub → `api-assitantbot`
- **Auto Deploy: ✅ ATIVAR**
- Port: `5555`
- Command: `celery -A app.workers.celery_app flower --port=5555`

### 4. Executar Migrações
No console do serviço API:
```bash
alembic upgrade head
```

### 5. Verificar
```bash
curl https://seu-dominio/health
```

## ✅ Pronto!

Agora toda vez que você fizer `git push`, o Easypanel vai:
1. Detectar mudança
2. Fazer build
3. Deploy automático
4. Reiniciar serviços

**Tempo: 2-5 minutos**

---

Veja **EASYPANEL-DEPLOY.md** para instruções completas!
