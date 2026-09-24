"""Configuration pytest pour les tests."""
import os

# Variables d'environnement pour les tests (avant d'importer l'app)
os.environ.setdefault("SECRET_KEY", "test-secret-key-minimum-32-chars-long-for-testing")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("DATABASE_URL_SYNC", "postgresql://test:test@localhost/test")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6379/0")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("MAC_SPOOF_DRY_RUN", "true")
os.environ.setdefault("ALLOWED_INTERFACES", '["eth0", "wlan0"]')
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "DEBUG")