import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def _env(name, default=None):
    value = os.environ.get(name, default)
    if value is None:
        raise ImproperlyConfigured(f"A variável de ambiente {name} é obrigatória.")
    return value


SECRET_KEY = _env("DJANGO_SECRET_KEY")
DEBUG = _env("DJANGO_DEBUG", "false").lower() in ("1", "true", "yes")
ALLOWED_HOSTS = [h.strip() for h in _env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Proteção de dados pessoais (ADR-0009): chave Fernet para cifrar campos sensíveis e
# chave HMAC para o hash determinístico usado na unicidade do CPF.
FIELD_ENCRYPTION_KEY = _env("FIELD_ENCRYPTION_KEY")
CPF_HASH_KEY = _env("CPF_HASH_KEY")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "shared",
    "tenancy",
    "people",
    "condominiums",
    "apartments",
    "owners",
    "residents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _env("POSTGRES_DB"),
        "USER": _env("POSTGRES_USER"),
        "PASSWORD": _env("POSTGRES_PASSWORD"),
        "HOST": _env("POSTGRES_HOST", "localhost"),
        "PORT": _env("POSTGRES_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

# Logs em stdout (decisão 6.1) com dados pessoais mascarados (ADR-0009).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"personal_data": {"()": "shared.logging.PersonalDataFilter"}},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["personal_data"],
        },
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    # Substitui os handlers padrão do Django, que não passariam pelo filtro.
    "loggers": {
        "django": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "django.server": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# Sem autenticação no MVP (ADR-0005): API aberta, sem SessionAuthentication e
# portanto sem exigência de CSRF na API. As páginas HTML mantêm o CSRF nativo.
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "UNAUTHENTICATED_USER": None,
    "EXCEPTION_HANDLER": "shared.http.api_exception_handler",
}
