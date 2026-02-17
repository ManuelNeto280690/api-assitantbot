# =========================
# Builder stage
# =========================
FROM python:3.11-slim AS builder

WORKDIR /app

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Instalar dependências Python no diretório do usuário
RUN pip install --no-cache-dir --user -r requirements.txt


# =========================
# Production stage
# =========================
FROM python:3.11-slim

# Criar usuário não-root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Instalar dependências de runtime (ANTES de trocar usuário)
RUN apt-get update && apt-get install -y \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependências Python do builder
COPY --from=builder /root/.local /home/appuser/.local

# Copiar código da aplicação
COPY --chown=appuser:appuser . .

# Variáveis de ambiente
ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Trocar para usuário seguro
USER appuser

# Expor porta
EXPOSE 8000

# Healthcheck simples
HEALTHCHECK CMD curl --fail http://localhost:8000/health || exit 1

# Rodar aplicação
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:8000"]
