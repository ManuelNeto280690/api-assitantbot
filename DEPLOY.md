# Multi-Tenant SaaS Backend - Guia de Deploy no Easypanel

## 🚀 Deploy Automático com GitHub + Easypanel

### Passo 1: Configurar GitHub

1. **Criar repositório no GitHub**:
   - Vá para https://github.com/new
   - Nome: `api-assitantbot` (ou outro nome)
   - Visibilidade: Private (recomendado por conter código de produção)
   - NÃO inicialize com README (já temos o código)

2. **Conectar repositório local ao GitHub**:
```bash
git remote add origin https://github.com/SEU-USUARIO/api-assitantbot.git
git branch -M main
git push -u origin main
```

### Passo 2: Configurar Easypanel

#### 2.1 Criar Novo Projeto

1. Acesse seu Easypanel
2. Clique em **"Create Project"**
3. Escolha **"GitHub"** como fonte
4. Autorize o Easypanel a acessar seu repositório
5. Selecione o repositório `api-assitantbot`

#### 2.2 Configurar Serviços

O Easypanel precisa de 5 serviços:

**Serviço 1: Redis**
- Tipo: Redis
- Nome: `redis`
- Versão: 7-alpine
- Porta: 6379

**Serviço 2: PostgreSQL** (opcional se usar Supabase)
- Tipo: PostgreSQL
- Nome: `postgres`
- Versão: 14
- Database: `saas_db`
- Username: `postgres`
- Password: (gere uma senha forte)

**Serviço 3: API (FastAPI)**
- Tipo: App
- Nome: `api`
- Build: Dockerfile
- Porta: 8000
- Comando: `gunicorn app.main:app -c gunicorn.conf.py`
- Variáveis de ambiente: (veja seção abaixo)

**Serviço 4: Celery Worker**
- Tipo: App
- Nome: `worker`
- Build: Dockerfile
- Comando: `celery -A app.workers.celery_app worker --loglevel=info`
- Variáveis de ambiente: (mesmas do API)

**Serviço 5: Celery Beat**
- Tipo: App
- Nome: `beat`
- Build: Dockerfile
- Comando: `celery -A app.workers.celery_app beat --loglevel=info`
- Variáveis de ambiente: (mesmas do API)

#### 2.3 Variáveis de Ambiente (para todos os serviços)

```env
# Application
APP_NAME=Multi-Tenant SaaS API
APP_ENV=production
DEBUG=False
SECRET_KEY=<GERE_UMA_CHAVE_FORTE>

# Supabase
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=<SUA_CHAVE>
SUPABASE_SERVICE_ROLE_KEY=<SUA_CHAVE>
SUPABASE_JWT_SECRET=<SEU_JWT_SECRET>

# Database (use Supabase ou PostgreSQL do Easypanel)
DATABASE_URL=postgresql+asyncpg://postgres:senha@postgres:5432/saas_db

# Redis (use o nome do serviço)
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

# APIs Externas
BREVO_API_KEY=<SUA_CHAVE>
VAPI_API_KEY=<SUA_CHAVE>

# Security
ENCRYPTION_KEY=<GERE_CHAVE_FERNET>
CORS_ORIGINS=https://seu-dominio.com

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

#### 2.4 Configurar Auto-Deploy

No Easypanel:
1. Vá para **Settings** do projeto
2. Ative **"Auto Deploy"**
3. Branch: `main`
4. Agora, toda vez que você fizer `git push`, o Easypanel vai:
   - Detectar mudanças
   - Fazer build da imagem Docker
   - Fazer deploy automático
   - Reiniciar os serviços

### Passo 3: Executar Migrações

Após o primeiro deploy:

1. Acesse o **Terminal** do serviço `api` no Easypanel
2. Execute:
```bash
alembic upgrade head
```

### Passo 4: Verificar Deploy

1. **Health Check**:
```bash
curl https://seu-dominio.com/health
```

2. **Documentação API**:
```
https://seu-dominio.com/docs
```

3. **Logs**:
   - Acesse os logs de cada serviço no Easypanel
   - Verifique se não há erros

## 🔄 Workflow de Desenvolvimento

### Fazer Alterações e Deploy Automático

```bash
# 1. Fazer alterações no código
# 2. Commitar
git add .
git commit -m "Descrição das alterações"

# 3. Push para GitHub
git push origin main

# 4. Easypanel detecta automaticamente e faz deploy!
# Aguarde 2-5 minutos para o build e deploy
```

### Rollback (se necessário)

```bash
# Voltar para commit anterior
git revert HEAD
git push origin main
```

## 📊 Monitoramento

### Logs em Tempo Real

No Easypanel:
- API: Ver logs do serviço `api`
- Workers: Ver logs do serviço `worker`
- Scheduler: Ver logs do serviço `beat`

### Métricas

- CPU e Memória: Dashboard do Easypanel
- Celery Tasks: Adicione Flower (opcional)

## 🔐 Segurança

### Checklist de Produção

- [ ] Variáveis de ambiente configuradas
- [ ] `DEBUG=False` em produção
- [ ] CORS configurado com domínios corretos
- [ ] SSL/HTTPS ativado
- [ ] Senhas fortes para banco de dados
- [ ] Backups automáticos configurados
- [ ] Rate limiting ativado
- [ ] Logs sendo monitorados

## 🆘 Troubleshooting

### Build Falha

1. Verifique os logs de build no Easypanel
2. Certifique-se que `requirements.txt` está correto
3. Verifique se o Dockerfile está na raiz

### Serviços Não Conectam

1. Verifique se os nomes dos serviços estão corretos
2. Redis: use `redis://redis:6379`
3. PostgreSQL: use `postgres:5432`

### Migrações Falharam

```bash
# No terminal do serviço API
alembic downgrade -1
alembic upgrade head
```

## 📝 Notas Importantes

1. **Nunca commite o arquivo `.env`** - ele está no `.gitignore`
2. **Use variáveis de ambiente do Easypanel** para configurações sensíveis
3. **Teste localmente antes de fazer push** para evitar builds quebrados
4. **Monitore os logs** após cada deploy

## 🎉 Pronto!

Agora você tem:
- ✅ Código no GitHub
- ✅ Deploy automático no Easypanel
- ✅ CI/CD configurado
- ✅ Toda alteração no código é automaticamente deployada

Basta fazer `git push` e aguardar o deploy automático! 🚀
