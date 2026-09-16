# MacBroken

Plateforme de gestion de MAC Spoofing — FastAPI + Celery + PostgreSQL + React.

## Prérequis

- Docker ≥ 24, Docker Compose v2
- Linux hôte recommandé (pour les capabilities `NET_ADMIN` du worker)

## Démarrage rapide

```bash
cp .env.example .env
# Éditer .env — notamment SECRET_KEY et POSTGRES_PASSWORD
openssl rand -hex 64   # → SECRET_KEY

# Démarrer la stack
docker compose up -d postgres redis backend worker
```

## Vérifications

# Vérifier la base de données
docker compose exec postgres psql -U mac_admin -d mac_spoofing -c "\dn"

# Vérifier la santé des conteneurs
docker compose ps

# Appliquer les migrations
docker compose exec backend alembic upgrade head

# Liveness
curl http://localhost:8000/api/v1/health/live

