"""
Django settings for anaplan project.

Configuração por variáveis de ambiente (estilo 12-factor) via django-environ.
Os valores reais vêm do ambiente ou de um arquivo .env na raiz (ver .env.example).
NENHUM segredo deve ser commitado neste arquivo.
"""

from pathlib import Path

import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuração por ambiente
# ---------------------------------------------------------------------------
env = environ.Env()
# Lê um arquivo .env na raiz do projeto, se existir (não é obrigatório).
environ.Env.read_env(BASE_DIR / ".env")

# SECURITY WARNING: defina DJANGO_SECRET_KEY no ambiente em produção!
# Gere uma nova com:
#   python -c "from django.core.management.utils import get_random_secret_key as k; print(k())"
SECRET_KEY = env("DJANGO_SECRET_KEY", default="dev-only-insecure-key-CHANGE-ME")

# SECURITY WARNING: nunca rode com DEBUG ligado em produção!
DEBUG = env.bool("DJANGO_DEBUG", default=False)

ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_select2',
    'integrador.apps.IntegradorConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'anaplan.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        "DIRS": [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'anaplan.wsgi.application'


# Database
# DATABASE_URL permite trocar SQLite (dev) por Postgres (produção) sem mexer no código.
# Ex.: DATABASE_URL=postgres://usuario:senha@host:5432/anaplan
DATABASES = {
    "default": env.db(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ---------------------------------------------------------------------------
# Marca do produto (neutra e configurável). Substitui referências fixas ao cliente.
# ---------------------------------------------------------------------------
PRODUCT_NAME = env("PRODUCT_NAME", default="Integrador de Planejamento")


# ---------------------------------------------------------------------------
# E-mail (notificações de carga) — usa o backend SMTP do Django.
# Se EMAIL_HOST estiver vazio, as notificações são silenciosamente ignoradas.
# ---------------------------------------------------------------------------
EMAIL_HOST = env("EMAIL_HOST", default="")
EMAIL_PORT = env.int("EMAIL_PORT", default=465)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="anaplan@example.com")
ANAPLAN_NOTIFY_RECIPIENTS = env.list("ANAPLAN_NOTIFY_RECIPIENTS", default=[])


# ---------------------------------------------------------------------------
# Integração Anaplan.
# NOTA: credencial única (mono-tenant). Temporário até o cofre de credenciais
# por tenant (Fase 1 do roadmap de produtização).
# ---------------------------------------------------------------------------
ANAPLAN_EMAIL = env("ANAPLAN_EMAIL", default="")
ANAPLAN_PASSWORD = env("ANAPLAN_PASSWORD", default="")
# Pasta de onde os arquivos a enviar são lidos (substitui o caminho fixo C:\\Temp\\IN).
ANAPLAN_IMPORT_DIR = env("ANAPLAN_IMPORT_DIR", default=str(BASE_DIR / "import_files"))


# ---------------------------------------------------------------------------
# Endurecimento de segurança para produção (aplicado quando DEBUG=False).
# ---------------------------------------------------------------------------
if not DEBUG:
    SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = env.int("DJANGO_SECURE_HSTS_SECONDS", default=2592000)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    CSRF_TRUSTED_ORIGINS = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])
