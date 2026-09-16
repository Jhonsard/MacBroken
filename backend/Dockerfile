# ============================================================
#  Backend FastAPI + Worker Celery — Multi-stage build
# ============================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

WORKDIR /app

# --- Dépendances système ---
# `iproute2` = binaire `ip` requis par le worker
# `curl`     = healthchecks
# `gcc`+`libpq` = build psycopg2 (retirés en stage final)
# --- Dépendances système ---
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        iproute2 \
        libcap2-bin \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# --- Capability NET_ADMIN sur le binaire `ip` (permet à appuser de l'exécuter) ---
RUN setcap cap_net_admin+ep "$(which ip)"

# --- Dépendances Python ---
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# --- Code applicatif ---
COPY . .

# --- Utilisateur non-root (sécurité) ---
RUN useradd --create-home --shell /bin/bash appuser \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Commande par défaut (surchargée par compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]