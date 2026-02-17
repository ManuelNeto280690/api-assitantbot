# Multi-Tenant SaaS Backend - FastAPI + Supabase

Enterprise-grade multi-tenant SaaS backend built with FastAPI, Supabase, PostgreSQL, and Celery.

## Features

✅ **Multi-Tenant Architecture** - Complete tenant isolation with row-level security  
✅ **Supabase Auth Integration** - JWT validation with automatic tenant context injection  
✅ **Campaign Engine** - Intelligent multi-channel campaigns (SMS, WhatsApp, Email, Voice)  
✅ **Smart Scheduling** - Timezone-aware scheduling with retry logic  
✅ **Async Workers** - Celery + Redis for background processing  
✅ **Channel Integrations** - Brevo (SMS/WhatsApp/Email) and VAPI (Voice)  
✅ **Automation System** - Event-driven workflows with triggers and actions  
✅ **Security** - RBAC, rate limiting, encryption, audit logs  
✅ **Production Ready** - Docker, health checks, structured logging

## Architecture

```
Frontend → Supabase Auth → FastAPI Backend → PostgreSQL
                                ↓
                         Celery Workers (Redis)
                                ↓
                    Brevo API / VAPI API
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- Supabase account

### Installation

1. **Clone and setup environment**

```bash
cd d:/api-assitantbot
cp .env.example .env
# Edit .env with your credentials
```

2. **Install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Setup database**

```bash
# Run migrations
alembic upgrade head
```

4. **Start services**

```bash
# Terminal 1: Start FastAPI
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2: Start Celery Worker
celery -A app.workers.celery_app worker --loglevel=info

# Terminal 3: Start Celery Beat (Scheduler)
celery -A app.workers.celery_app beat --loglevel=info

# Terminal 4: Start Redis (if not running)
redis-server
```

### Docker Deployment

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Configuration

### Environment Variables

Key environment variables (see `.env.example` for full list):

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db

# Redis
REDIS_URL=redis://localhost:6379/0

# API Keys
BREVO_API_KEY=your-brevo-key
VAPI_API_KEY=your-vapi-key
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Authentication

All API requests require a Supabase JWT token:

```bash
curl -H "Authorization: Bearer YOUR_SUPABASE_JWT" \
     http://localhost:8000/api/v1/leads
```

The backend automatically:
1. Validates the JWT
2. Extracts `user_id`
3. Looks up tenant membership
4. Injects tenant context

**CRITICAL**: Never trust `tenant_id` from frontend - always derived from JWT.

## Key Endpoints

### Tenants
- `POST /api/v1/tenants` - Create tenant (super admin)
- `GET /api/v1/tenants/current` - Get current tenant
- `POST /api/v1/tenants/current/memberships` - Add user to tenant

### Leads
- `POST /api/v1/leads` - Create lead
- `GET /api/v1/leads` - List leads (with filters)
- `PATCH /api/v1/leads/{id}` - Update lead
- `DELETE /api/v1/leads/{id}` - Soft delete lead

### Campaigns
- `POST /api/v1/campaigns` - Create campaign
- `GET /api/v1/campaigns` - List campaigns
- `POST /api/v1/campaigns/{id}/start` - Start campaign
- `POST /api/v1/campaigns/{id}/pause` - Pause campaign

### Webhooks
- `POST /api/v1/webhooks/brevo/sms` - Brevo SMS webhook
- `POST /api/v1/webhooks/brevo/email` - Brevo email webhook
- `POST /api/v1/webhooks/vapi/call-status` - VAPI call status

## Campaign System

### Creating a Campaign

```python
{
  "name": "Welcome Campaign",
  "channel": "sms",
  "lead_list_id": "uuid",
  "start_datetime": "2024-12-01T09:00:00Z",
  "timezone": "America/New_York",
  "message_content": {
    "body": "Welcome to our service!"
  },
  "retry_strategy": {
    "max_attempts": 3,
    "delays_minutes": [30, 120, 360]
  }
}
```

### Schedule Rules

```python
{
  "start_hour": 9,
  "end_hour": 17,
  "days_allowed": [0, 1, 2, 3, 4],  # Monday-Friday
  "blackout_dates": ["2024-12-25", "2024-01-01"]
}
```

### Voice Call Retry Logic

- `busy` → Retry in 30 minutes
- `no_answer` → Retry in 2 hours
- `voicemail` → Mark as completed
- `failed` → Mark as failed

## Automation System

### Event Types

- `lead_created`
- `lead_updated`
- `message_received`
- `campaign_completed`
- `voice_failed`
- `voice_completed`
- `scheduled_time`

### Creating an Automation

Automations follow: **Trigger → Conditions → Actions**

Example: Send welcome email when lead is created with "vip" tag

```python
{
  "name": "VIP Welcome",
  "trigger_type": "lead_created",
  "conditions": [
    {
      "condition_type": "tag_has",
      "condition_config": {"tag": "vip"}
    }
  ],
  "actions": [
    {
      "action_type": "send_email",
      "action_config": {
        "subject": "Welcome VIP!",
        "body": "Thank you for joining..."
      },
      "delay_seconds": 0
    }
  ]
}
```

## Security

### Multi-Tenant Isolation

- All tables include `tenant_id`
- Indexed for performance
- Never trust frontend `tenant_id`
- Always derive from JWT → membership

### RBAC Roles

- `super_admin` - Full system access
- `tenant_admin` - Full tenant access
- `operator` - Create/update resources
- `viewer` - Read-only access

### Rate Limiting

- Per tenant
- Per channel
- Sliding window algorithm
- Redis-backed

### Encryption

External API tokens stored encrypted using Fernet.

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

### Celery Monitoring (Flower)

```bash
# Access Flower UI
http://localhost:5555
```

### Logs

Structured JSON logging in production:

```json
{
  "event": "Created lead",
  "tenant_id": "uuid",
  "lead_id": "uuid",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Database Migrations

### Create Migration

```bash
alembic revision --autogenerate -m "Add new table"
```

### Apply Migrations

```bash
alembic upgrade head
```

### Rollback

```bash
alembic downgrade -1
```

## Scaling

### Horizontal Scaling

- **API**: Stateless, scale with load balancer
- **Workers**: Add more Celery workers
- **Database**: PostgreSQL read replicas
- **Redis**: Redis Cluster for high availability

### Performance Tips

1. Use database indexes on `tenant_id`
2. Implement caching for frequently accessed data
3. Use connection pooling
4. Monitor slow queries
5. Implement pagination for large datasets

## Troubleshooting

### Workers not processing tasks

```bash
# Check Celery worker status
celery -A app.workers.celery_app inspect active

# Check Redis connection
redis-cli ping
```

### Database connection issues

```bash
# Test database connection
python -c "from app.database import engine; import asyncio; asyncio.run(engine.connect())"
```

### JWT validation failing

- Verify `SUPABASE_JWT_SECRET` matches your Supabase project
- Check token expiration
- Ensure token format is correct

## Development

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black app/

# Lint
flake8 app/

# Type checking
mypy app/
```

## License

MIT License

## Support

For issues and questions, please open an issue on GitHub.
