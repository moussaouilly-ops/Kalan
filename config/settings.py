"""
Configuration Django — Plateforme e-learning (Django + DRF + PostgreSQL + JWT).
"""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ---------------------------------------------------------------------------
# Sécurité — en production, TOUTES ces valeurs doivent venir de variables
# d'environnement (voir .env.example). Ne jamais committer de vraies clés.
# ---------------------------------------------------------------------------
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "changeme-en-dev-uniquement")
DEBUG = os.environ.get("DJANGO_DEBUG", "True") == "True"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",  # recherche full-text (SearchVector, trigram...)
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    "core",
    "accounts",
    "courses",
    "payments",
    "quizzes",
    "reviews",
    "messaging",
    "affiliates",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Base de données
# Par défaut : SQLite, pour démarrer sans rien installer (fichier db.sqlite3
# créé automatiquement à côté de manage.py).
# Pour passer sur PostgreSQL (recommandé avant la mise en ligne réelle),
# mettre USE_POSTGRES=True dans le fichier .env et renseigner les DB_*.
# ---------------------------------------------------------------------------
if os.environ.get("USE_POSTGRES", "False") == "True":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "elearning_db"),
            "USER": os.environ.get("DB_USER", "elearning_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "changeme"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ---------------------------------------------------------------------------
# Validation des mots de passe
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 8}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Ouagadougou"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Fichiers statiques et médias (vidéos, PDF, images de cours)
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# En production : basculer vers un stockage cloud (S3-compatible, ex: OVH,
# Backblaze B2, ou AWS S3) via django-storages plutôt que le disque local.
# DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth": "10/min",
        "payment_initiate": "6/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ---------------------------------------------------------------------------
# CORS — en développement (DEBUG=True), on autorise toutes les origines pour
# simplifier les tests locaux (ex: ouvrir un fichier HTML statique en
# file://, ou tester depuis un port différent). En production, retirer
# CORS_ALLOW_ALL_ORIGINS et ne garder que CORS_ALLOWED_ORIGINS ci-dessous.
# ---------------------------------------------------------------------------
if DEBUG:
    CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173"
).split(",")
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Paramètres métier propres à la plateforme
# ---------------------------------------------------------------------------
PLATFORM_COMMISSION_PERCENT_DEFAULT = 20  # commission plateforme sur les ventes formateurs
DEFAULT_AFFILIATE_COMMISSION_PERCENT = 10
CURRENCY = "XOF"  # Franc CFA (UEMOA)

# Paiement mobile money — contrat direct par opérateur. Chaque bloc est
# rempli via variables d'environnement une fois le contrat signé avec
# l'opérateur concerné. Orange Money et Wave suivent une documentation
# publique officielle (voir payments/providers/) ; Moov Money et Coris Money
# nécessitent la documentation fournie par l'opérateur après souscription.
MOBILE_MONEY_PROVIDERS = {
    "orange_money": {
        # "auth_header" = base64(client_id:client_secret), fourni par
        # developer.orange.com après souscription à l'offre Web Payment.
        "auth_header": os.environ.get("ORANGE_MONEY_AUTH_HEADER", ""),
        "merchant_key": os.environ.get("ORANGE_MONEY_MERCHANT_KEY", ""),
        "country_code": os.environ.get("ORANGE_MONEY_COUNTRY_CODE", "bf"),
    },
    "wave": {
        "api_key": os.environ.get("WAVE_API_KEY", ""),
    },
    "moov_money": {
        "base_url": os.environ.get("MOOV_MONEY_BASE_URL", ""),
        "merchant_key": os.environ.get("MOOV_MONEY_MERCHANT_KEY", ""),
    },
    "coris_money": {
        "base_url": os.environ.get("CORIS_MONEY_BASE_URL", ""),
        "merchant_key": os.environ.get("CORIS_MONEY_MERCHANT_KEY", ""),
    },
}

# PayDunya reste configuré en option (agrégateur de secours — voir
# payments/paydunya.py), au cas où un contrat direct prendrait du temps à
# obtenir.
PAYDUNYA = {
    "master_key": os.environ.get("PAYDUNYA_MASTER_KEY", ""),
    "private_key": os.environ.get("PAYDUNYA_PRIVATE_KEY", ""),
    "public_key": os.environ.get("PAYDUNYA_PUBLIC_KEY", ""),
    "token": os.environ.get("PAYDUNYA_TOKEN", ""),
    "mode": os.environ.get("PAYDUNYA_MODE", "test"),  # "test" ou "live"
}

EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@example.com")

FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
