# 🚀 Guia Completo: Deploy Automático GitHub → Easypanel

## 📋 Pré-requisitos

- ✅ Código no GitHub (repositório: `ManuelNeto280690/api-assitantbot`)
- ✅ Conta no Easypanel
- ✅ Credenciais do Supabase

---

## Passo 1: Conectar GitHub ao Easypanel

### 1.1 Acessar Easypanel
1. Faça login no seu Easypanel
2. Vá para **Projects**

### 1.2 Criar Novo Projeto
1. Clique em **"+ Create Project"**
2. Nome do projeto: `api-assitantbot`
3. Clique em **"Create"**

### 1.3 Conectar ao GitHub
1. Dentro do projeto, clique em **"+ Create Service"**
2. Escolha **"App"**
3. Em **Source**, selecione **"GitHub"**
4. Se for a primeira vez:
   - Clique em **"Connect GitHub"**
   - Autorize o Easypanel a acessar seus repositórios
   - Selecione **"Only select repositories"**
   - Escolha `api-assitantbot`
   - Clique em **"Install & Authorize"**

---

## Passo 2: Configurar Serviços

Você precisa criar **5 serviços**. Vou mostrar cada um:

### 🔴 Serviço 1: Redis

1. Clique em **"+ Create Service"**
2. Escolha **"Database"** → **"Redis"**
3. Configurações:
   - **Name**: `redis`
   - **Version**: `7-alpine`
4. Clique em **"Create"**

### 🟢 Serviço 2: API (FastAPI)

1. Clique em **"+ Create Service"**
2. Escolha **"App"**
3. Configurações básicas:
   - **Name**: `api`
   - **Source**: GitHub
   - **Repository**: `ManuelNeto280690/api-assitantbot`
   - **Branch**: `main`
   - **Auto Deploy**: ✅ **ATIVE ISSO** (muito importante!)

4. **Build Settings**:
   - **Build Type**: Dockerfile
   - **Dockerfile Path**: `./Dockerfile`

5. **Deploy Settings**:
   - **Port**: `8000`
   - **Command**: `gunicorn app.main:app -c gunicorn.conf.py`

6. **Environment Variables** (clique em "Add Variable" para cada):

```env
APP_NAME=Multi-Tenant SaaS API
APP_ENV=production
DEBUG=False
SECRET_KEY=GERE_UMA_CHAVE_FORTE_AQUI
HOST=0.0.0.0
PORT=8000
WORKERS=4

# Supabase (SUBSTITUA com suas credenciais)
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=sua-chave-anon
SUPABASE_SERVICE_ROLE_KEY=sua-chave-service-role
SUPABASE_JWT_SECRET=seu-jwt-secret

# Database (Supabase com AsyncPG)
# 1. Vá em Project Settings -> Database -> Connection Pooling
# 2. Copie a string "URI" (Mode: Transaction, Port: 6543)
# 3. Substitua 'postgres://' por 'postgresql+asyncpg://'
# 4. Substitua '[YOUR-PASSWORD]' pela sua senha real
DATABASE_URL=postgresql+asyncpg://postgres.[REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=10

# Redis (use o nome do serviço)
REDIS_URL=redis://redis:6379/0
REDIS_MAX_CONNECTIONS=50

# Celery
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# Brevo (SUBSTITUA com suas chaves)
BREVO_API_KEY=sua-chave-brevo
BREVO_SMS_SENDER=SeuNome
BREVO_EMAIL_SENDER=noreply@seudominio.com

# VAPI (SUBSTITUA com sua chave)
VAPI_API_KEY=sua-chave-vapi
VAPI_PHONE_NUMBER=+1234567890

# Security
ENCRYPTION_KEY=GERE_CHAVE_FERNET_AQUI
CORS_ORIGINS=https://seudominio.com,https://app.seudominio.com

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Features
ENABLE_AUDIT_LOGS=True
ENABLE_RATE_LIMITING=True
ENABLE_CIRCUIT_BREAKER=True

# Monitoring
LOG_LEVEL=INFO
```

7. **Domains** (opcional):
   - Adicione seu domínio personalizado
   - Ou use o domínio gerado pelo Easypanel

8. Clique em **"Create"**

### 🟡 Serviço 3: Celery Worker

1. Clique em **"+ Create Service"**
2. Escolha **"App"**
3. Configurações:
   - **Name**: `worker`
   - **Source**: GitHub
   - **Repository**: `ManuelNeto280690/api-assitantbot`
   - **Branch**: `main`
   - **Auto Deploy**: ✅ ATIVE

4. **Build Settings**:
   - **Build Type**: Dockerfile
   - **Dockerfile Path**: `./Dockerfile`

5. **Deploy Settings**:
   - **Command**: `celery -A app.workers.celery_app worker --loglevel=info`
   - **Port**: (deixe vazio, não precisa)

6. **Environment Variables**:
   - Copie TODAS as mesmas variáveis do serviço `api`

7. Clique em **"Create"**

### 🟠 Serviço 4: Celery Beat (Scheduler)

1. Clique em **"+ Create Service"**
2. Escolha **"App"**
3. Configurações:
   - **Name**: `beat`
   - **Source**: GitHub
   - **Repository**: `ManuelNeto280690/api-assitantbot`
   - **Branch**: `main`
   - **Auto Deploy**: ✅ ATIVE

4. **Build Settings**:
   - **Build Type**: Dockerfile
   - **Dockerfile Path**: `./Dockerfile`

5. **Deploy Settings**:
   - **Command**: `celery -A app.workers.celery_app beat --loglevel=info`
   - **Port**: (deixe vazio)

6. **Environment Variables**:
   - Copie TODAS as mesmas variáveis do serviço `api`

7. Clique em **"Create"**

### 🔵 Serviço 5: Flower (Monitoramento - Opcional)

1. Clique em **"+ Create Service"**
2. Escolha **"App"**
3. Configurações:
   - **Name**: `flower`
   - **Source**: GitHub
   - **Repository**: `ManuelNeto280690/api-assitantbot`
   - **Branch**: `main`
   - **Auto Deploy**: ✅ ATIVE

4. **Deploy Settings**:
   - **Port**: `5555`
   - **Command**: `celery -A app.workers.celery_app flower --port=5555`

5. **Environment Variables**:
   - Copie as variáveis do `api`

---

## Passo 3: Executar Migrações do Banco de Dados

Após todos os serviços estarem rodando:

1. Vá para o serviço **`api`**
2. Clique em **"Console"** ou **"Terminal"**
3. Execute:

```bash
alembic upgrade head
```

---

## Passo 4: Verificar Deploy

### 4.1 Health Check
```bash
curl https://seu-dominio.easypanel.io/health
```

Resposta esperada:
```json
{
  "status": "healthy",
  "app": "Multi-Tenant SaaS API",
  "env": "production"
}
```

### 4.2 Documentação da API
Acesse: `https://seu-dominio.easypanel.io/docs`

### 4.3 Verificar Logs
- Vá em cada serviço
- Clique em **"Logs"**
- Verifique se não há erros

---

## 🔄 Como Funciona o Auto-Deploy

### Fluxo Automático

```
1. Você faz alterações no código
2. git add .
3. git commit -m "Descrição"
4. git push origin main
   ↓
5. GitHub recebe o push
   ↓
6. Easypanel detecta mudança (webhook)
   ↓
7. Easypanel faz build da imagem Docker
   ↓
8. Easypanel faz deploy automático
   ↓
9. Serviços são reiniciados
   ↓
10. ✅ Código atualizado em produção!
```

**Tempo total**: 2-5 minutos

### Testar Auto-Deploy

1. Faça uma pequena alteração:
```python
# Em app/main.py, altere a versão
@app.get("/")
async def root():
    return {
        "message": "Multi-Tenant SaaS API",
        "version": "1.0.1",  # Altere aqui
        "docs": "/docs" if settings.debug else None,
    }
```

2. Commit e push:
```bash
git add app/main.py
git commit -m "Update version to 1.0.1"
git push origin main
```

3. Aguarde 2-5 minutos

4. Verifique:
```bash
curl https://seu-dominio.easypanel.io/
```

Deve mostrar `"version": "1.0.1"`

---

## 🔐 Gerar Chaves de Segurança

### SECRET_KEY
```python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### ENCRYPTION_KEY (Fernet)
```python
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## 📊 Monitoramento

### Logs em Tempo Real
- No Easypanel, vá em cada serviço
- Clique em **"Logs"**
- Veja logs em tempo real

### Métricas
- CPU e Memória: Dashboard do Easypanel
- Celery Tasks: Acesse o Flower em `https://flower.seudominio.com`

### Alertas (Opcional)
Configure no Easypanel:
- Alertas de CPU alta
- Alertas de memória
- Alertas de serviço down

---

## 🆘 Troubleshooting

### Build Falha
1. Verifique logs de build no Easypanel
2. Certifique-se que `Dockerfile` está correto
3. Verifique `requirements.txt`

### Serviço Não Inicia
1. Verifique logs do serviço
2. Verifique variáveis de ambiente
3. Verifique se Redis está rodando

### Migrações Falharam
```bash
# No console do serviço API
alembic current
alembic downgrade -1
alembic upgrade head
```

### Auto-Deploy Não Funciona
1. Verifique se "Auto Deploy" está ativado
2. Verifique se o webhook do GitHub está configurado
3. Em Settings do serviço, veja "Deployments"

---

## ✅ Checklist Final

- [ ] Redis criado e rodando
- [ ] Serviço API criado com Auto-Deploy ativado
- [ ] Serviço Worker criado com Auto-Deploy ativado
- [ ] Serviço Beat criado com Auto-Deploy ativado
- [ ] Todas as variáveis de ambiente configuradas
- [ ] Migrações executadas (`alembic upgrade head`)
- [ ] Health check funcionando
- [ ] Documentação acessível em `/docs`
- [ ] Logs sem erros
- [ ] Teste de auto-deploy realizado

---

## 🎉 Pronto!

Agora você tem:
- ✅ Código no GitHub
- ✅ Deploy automático configurado
- ✅ Toda alteração no código é automaticamente deployada
- ✅ Monitoramento em tempo real

**Basta fazer `git push` e aguardar 2-5 minutos!** 🚀

---

## 📝 Comandos Úteis

```bash
# Ver status do Git
git status

# Fazer alterações e deploy
git add .
git commit -m "Descrição das alterações"
git push origin main

# Ver logs do último commit
git log -1

# Reverter último commit (se necessário)
git revert HEAD
git push origin main
```

---

## 🔗 Links Úteis

- **Easypanel Docs**: https://easypanel.io/docs
- **Supabase Dashboard**: https://app.supabase.com
- **GitHub Repo**: https://github.com/ManuelNeto280690/api-assitantbot
