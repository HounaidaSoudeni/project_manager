from pathlib import Path
from datetime import timedelta
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env('SECRET_KEY')
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
    'users',
    'projects',
    'kanban',
    'ai_assistant',
    'analytics',
    'notifications',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates','DIRS': [BASE_DIR / 'templates'],'APP_DIRS': True,'OPTIONS': {'context_processors': ['django.template.context_processors.debug','django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages',],},},]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3','NAME': BASE_DIR / 'db.sqlite3',}}
AUTH_USER_MODEL = 'users.CustomUser'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ('rest_framework_simplejwt.authentication.JWTAuthentication',),
    'DEFAULT_PERMISSION_CLASSES': ('rest_framework.permissions.IsAuthenticated',),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend','rest_framework.filters.SearchFilter','rest_framework.filters.OrderingFilter',],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': ['rest_framework.throttling.UserRateThrottle'],
    'DEFAULT_THROTTLE_RATES': {'user': '200/hour'},
}

SIMPLE_JWT = {'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),'REFRESH_TOKEN_LIFETIME': timedelta(days=7),'ROTATE_REFRESH_TOKENS': True,}
SPECTACULAR_SETTINGS = {'TITLE': 'Project Manager API','DESCRIPTION': 'API REST — Plateforme intelligente de gestion de projets (ING3 École Sesame)','VERSION': '1.0.0','SERVE_INCLUDE_SCHEMA': False,}
CORS_ALLOW_ALL_ORIGINS = True
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Tunis'
USE_I18N = True
USE_TZ = True