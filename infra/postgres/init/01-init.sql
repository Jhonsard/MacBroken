-- ============================================================
--  Initialisation PostgreSQL — MAC Spoofing Platform
--  Exécuté automatiquement au premier démarrage du container
-- ============================================================

-- Extensions requises
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";   -- emails case-insensitive

-- Timezone cohérente
ALTER DATABASE mac_spoofing SET timezone TO 'UTC';

-- ------------------------------------------------------------
-- Schéma applicatif dédié (isolation logique)
-- ------------------------------------------------------------
CREATE SCHEMA IF NOT EXISTS app;

COMMENT ON SCHEMA app IS 'Schéma principal de la plateforme MAC Spoofing';

-- ------------------------------------------------------------
-- Rôle applicatif à privilèges limités (bonne pratique)
-- L'utilisateur POSTGRES_USER reste superuser pour les migrations
-- ------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'mac_app') THEN
        CREATE ROLE mac_app WITH LOGIN PASSWORD 'CHANGE_ME_app_password';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE mac_spoofing TO mac_app;
GRANT USAGE  ON SCHEMA app            TO mac_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mac_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA app
    GRANT USAGE, SELECT ON SEQUENCES TO mac_app;

-- ------------------------------------------------------------
-- Table de suivi des migrations (Alembic utilisera public)
-- ------------------------------------------------------------
-- (Alembic gère sa propre table alembic_version)
