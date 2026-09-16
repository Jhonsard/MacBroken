<<<<<<< HEAD
# MAC Spoofing Platform

Plateforme de gestion de MAC Spoofing — FastAPI + Celery + PostgreSQL + React.

## Prérequis

- Docker ≥ 24, Docker Compose v2
- Linux hôte recommandé (pour les capabilities `NET_ADMIN` du worker)

## Démarrage rapide

```bash
cp .env.example .env
# Éditer .env — notamment SECRET_KEY et POSTGRES_PASSWORD
openssl rand -hex 64   # → SECRET_KEY

# Démarrer la stack (sans frontend/ni flower)
docker compose up -d postgres redis backend worker
```

## Vérifications

```bash

# PostgreSQL répond à
# List of schemas
#  Name  |       Owner       
#--------+-------------------
 #app    | mac_admin
 #public | pg_database_owner
#(2 rows)

docker compose exec postgres psql -U mac_admin -d mac_spoofing -c "\dn" # (schéma app présent)

# Vérifier la santé
docker compose ps

# connection a la bd
docker compose exec backend alembic upgrade head

# Liveness
curl http://localhost:8000/api/v1/health/live
# → {"status":"ok","service":"MAC Spoofing Platform","env":"development"}

# Readiness (DB)
curl http://localhost:8000/api/v1/health/ready
# → {"status":"ok","checks":{"database":"ok"}}

# Swagger (dev uniquement)
open http://localhost:8000/docs
```

## Reconfiguration 

```bash
# 1. Reconstruire l'image backend (requirements.txt a changé)
docker compose build backend worker

# 2. Redémarrer la stack
docker compose up -d postgres redis backend worker

# 3. Appliquer la migration initiale
docker compose exec backend alembic upgrade head

# 4. Vérifier les tables
docker compose exec postgres psql -U mac_admin -d mac_spoofing -c "\dt"
# Doit afficher : alembic_version, users, mac_history, chat_logs

# migrations alembic
docker compose exec backend alembic upgrade head
```
## Structure

Voir `Guide.md` — architecture 3-tiers modulaire.
=======
# MacBroken
>>>>>>> c3629b7d22254433faab9e078ea1b8f3c3fd2e2a
