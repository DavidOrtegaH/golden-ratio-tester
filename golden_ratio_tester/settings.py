import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.environ.get('DJANGO_DEBUG', '0') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise RuntimeError('DJANGO_SECRET_KEY must be set in production')
    SECRET_KEY = secrets.token_urlsafe(48)
if not DEBUG and (len(SECRET_KEY) < 50 or len(set(SECRET_KEY)) < 5
                  or SECRET_KEY.startswith(('replace', 'django-insecure-'))):
    raise RuntimeError('DJANGO_SECRET_KEY must be a strong, unique production secret of at least 50 characters')
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]').split(',')
INSTALLED_APPS = ['django.contrib.staticfiles', 'lab']
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'lab.middleware.PrivacyHeaders',
    'lab.middleware.RequestLimits',
    'django.middleware.common.CommonMiddleware',
    'lab.csrf.PreviewRequestMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'golden_ratio_tester.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates',
              'DIRS': [], 'APP_DIRS': True,
              'OPTIONS': {'context_processors': ['django.template.context_processors.request']}}]
WSGI_APPLICATION = 'golden_ratio_tester.wsgi.application'
DATABASES = {}
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []
STORAGES = {'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage' if DEBUG
                           else 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 11 * 1024 * 1024
FILE_UPLOAD_HANDLERS = ['lab.uploads.BoundedMemoryUploadHandler']
DATA_UPLOAD_MAX_NUMBER_FILES = 1
DATA_UPLOAD_MAX_NUMBER_FIELDS = 8
ANALYSIS_RATE_LIMIT = int(os.environ.get('ANALYSIS_RATE_LIMIT', '6'))
CSRF_FAILURE_VIEW = 'lab.responses.csrf_failure'
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_AGE = None
SECURE_SSL_REDIRECT = not DEBUG
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
LOGGING = {
    'version': 1, 'disable_existing_loggers': False,
    'filters': {'private_urls': {'()': 'lab.logging.RedactResultURLs'}},
    'handlers': {'console': {'class': 'logging.StreamHandler', 'filters': ['private_urls']}},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'django.server': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
    },
}
