# -*- coding: utf-8 -*-
"""Configuración del sistema de ingesta de datos SEN.

Toda credencial y parámetro dependiente del entorno se lee de variables de
entorno. El módulo falla de forma explícita al arrancar si falta un valor
sensible, en lugar de recurrir a un valor por defecto: los defaults silenciosos
son la causa de que credenciales de producción terminen versionadas.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DJANGO_DEBUG=(bool, False),
    DJANGO_ALLOWED_HOSTS=(list, []),
    CORS_ALLOWED_ORIGINS=(list, []),
    CSRF_TRUSTED_ORIGINS=(list, []),
    SECURE_SSL_REDIRECT=(bool, True),
)

environ.Env.read_env(BASE_DIR / '.env')

# --- Núcleo -----------------------------------------------------------------
# Sin valor por defecto: si SECRET_KEY no está definida, el proceso no arranca.
SECRET_KEY = env('DJANGO_SECRET_KEY')
DEBUG = env('DJANGO_DEBUG')
ALLOWED_HOSTS = env('DJANGO_ALLOWED_HOSTS')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'ingestion',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# --- Base de datos ----------------------------------------------------------
# Comparte el motor PostgreSQL del Data Warehouse para que el BI consuma la
# tabla de ingesta sin exportaciones intermedias.
DATABASES = {'default': env.db('DATABASE_URL')}
DATABASES['default']['CONN_MAX_AGE'] = env.int('DB_CONN_MAX_AGE', default=60)

if 'postgresql' in DATABASES['default']['ENGINE']:
    # TLS obligatorio por defecto: el Data Warehouse está en una instancia
    # gestionada a la que se llega por red pública.
    DATABASES['default']['OPTIONS'] = {
        'sslmode': env('DB_SSLMODE', default='require'),
    }

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Caché ------------------------------------------------------------------
# Respalda los contadores de las cuotas de tasa. La caché local en memoria
# alcanza para un único proceso; con varias instancias detrás de un balanceador
# es imprescindible un backend compartido (Redis), o cada instancia llevaría su
# propio contador y el límite real sería N veces el configurado.
CACHES = {
    'default': env.cache(
        'CACHE_URL',
        default='locmemcache://ingesta',
    ),
}

# --- Autenticación ----------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12},
    },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# --- API --------------------------------------------------------------------
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    # Cierre por defecto: cada vista debe abrir el acceso explícitamente.
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'ingestion.pagination.PaginacionEstandar',
    'PAGE_SIZE': 25,
    'DEFAULT_THROTTLE_CLASSES': (
        'ingestion.throttling.LecturaThrottle',
    ),
    'DEFAULT_THROTTLE_RATES': {
        'lectura': env('THROTTLE_LECTURA', default='180/min'),
        'escritura': env('THROTTLE_ESCRITURA', default='40/min'),
        'autenticacion': env('THROTTLE_AUTENTICACION', default='5/min'),
    },
    # Cantidad de proxies inversos por delante de la aplicación. Declararla
    # evita que un cliente falsee su IP enviando X-Forwarded-For y así eluda
    # las cuotas por dirección.
    'NUM_PROXIES': env.int('NUM_PROXIES', default=1),
    'DEFAULT_RENDERER_CLASSES': (
        ('rest_framework.renderers.JSONRenderer',)
        + (('rest_framework.renderers.BrowsableAPIRenderer',) if DEBUG else ())
    ),
    'DEFAULT_PARSER_CLASSES': ('rest_framework.parsers.JSONParser',),
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(hours=8),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('JWT_SIGNING_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# --- CORS y CSRF ------------------------------------------------------------
# Lista blanca explícita. Nunca se habilita CORS_ALLOW_ALL_ORIGINS: con
# CORS_ALLOW_CREDENTIALS activo equivale a exponer la API a cualquier origen.
CORS_ALLOWED_ORIGINS = env('CORS_ALLOWED_ORIGINS')
CORS_ALLOW_CREDENTIALS = False
CORS_ALLOW_METHODS = ('GET', 'POST', 'PATCH', 'OPTIONS')
CORS_ALLOW_HEADERS = (
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
)
CSRF_TRUSTED_ORIGINS = env('CSRF_TRUSTED_ORIGINS')

# --- Endurecimiento HTTP ----------------------------------------------------
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
CSRF_COOKIE_HTTPONLY = False  # El frontend necesita leerla para el header.
CSRF_COOKIE_SAMESITE = 'Strict'

if not DEBUG:
    SECURE_SSL_REDIRECT = env('SECURE_SSL_REDIRECT')
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_HSTS_SECONDS = 31_536_000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Acota el tamaño del cuerpo y la cantidad de campos por petición para limitar
# el agotamiento de recursos por payloads inflados.
DATA_UPLOAD_MAX_MEMORY_SIZE = 1_048_576  # 1 MiB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 200

# --- Internacionalización ---------------------------------------------------
LANGUAGE_CODE = 'es-py'
TIME_ZONE = 'America/Asuncion'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# --- Registro de eventos ----------------------------------------------------
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detallado': {
            'format': '{asctime} {levelname} {name} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'consola': {
            'class': 'logging.StreamHandler',
            'formatter': 'detallado',
        },
    },
    'root': {'handlers': ['consola'], 'level': 'INFO'},
    'loggers': {
        # Deja rastro de intentos de acceso fallidos y peticiones rechazadas.
        'django.security': {'handlers': ['consola'], 'level': 'WARNING'},
        'ingestion': {'handlers': ['consola'], 'level': 'INFO'},
    },
}
