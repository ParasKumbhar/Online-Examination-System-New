"""
Django settings with environment-based configuration.
Security hardened for production.
"""

from pathlib import Path
import os
from django.contrib import messages
import sys

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR.parent, '.env'))

# Security Configuration
SECRET_KEY = os.environ.get('SECRET_KEY', 'INSECURE-DEVELOPMENT-KEY-CHANGE-IN-PRODUCTION')
DEBUG = os.environ.get('DEBUG', 'False') == 'True'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_ratelimit',
    'admission',
    'student',
    'tuition',
    'course',
    'resultprocessing',
    'studentPreferences',
    'questions',
    'faculty',
    'api',  # New API app
    'notifications',  # New notifications app
    'auditlog',  # New audit logging app
    'openpyxl',
    'pandas',
]

# Middleware - Order matters!
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.AuditLoggingMiddleware',  # Custom audit middleware
    'core.middleware.SecurityHeadersMiddleware',  # Custom security headers
    'core.middleware.RateLimitMiddleware',  # Custom rate limiting
]

ROOT_URLCONF = 'examProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
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

WSGI_APPLICATION = 'examProject.wsgi.application'

# Database Configuration
if os.environ.get('DATABASE_ENGINE') == 'django.db.backends.postgresql':
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get('DATABASE_ENGINE', 'django.db.backends.postgresql'),
            'NAME': os.environ.get('DATABASE_NAME', 'exam_system'),
            'USER': os.environ.get('DATABASE_USER', 'postgres'),
            'PASSWORD': os.environ.get('DATABASE_PASSWORD', ''),
            'HOST': os.environ.get('DATABASE_HOST', 'localhost'),
            'PORT': os.environ.get('DATABASE_PORT', '5432'),
            'CONN_MAX_AGE': 600,
            'OPTIONS': {
                'connect_timeout': 10,
                'options': '-c default_transaction_isolation=read_committed'
            }
        }
    }
else:
    # Fallback to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password Validation
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Increased from 9
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Calcutta'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static Files
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'examProject/static')
]
STATIC_ROOT = os.path.join(BASE_DIR, 'static')

# Media Files
MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'

# Messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# Email Configuration
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@examsystem.com')

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    },
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.AcceptHeaderVersioning',
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
}

# CORS Configuration
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:8000').split(',')
CORS_ALLOW_CREDENTIALS = True

# Security Settings
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_SECURITY_POLICY = {
        'default-src': ("'self'",),
        'script-src': ("'self'", "'unsafe-inline'", "'unsafe-eval'"),
        'style-src': ("'self'", "'unsafe-inline'"),
        'img-src': ("'self'", "data:", "https:"),
        'font-src': ("'self'", "data:"),
        'connect-src': ("'self'", "https:"),
        'frame-ancestors': ("'self'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
    }
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Session Configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f"redis://{os.environ.get('REDIS_HOST', 'localhost')}:{os.environ.get('REDIS_PORT', 6379)}/0",
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/exam_system.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'json',
        },
        'console': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/security.log'),
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'formatter': 'json',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'security': {
            'handlers': ['security'],
            'level': 'WARNING',
            'propagate': False,
        },
        'app': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
    },
}

# Rate Limiting
RATE_LIMIT_CONFIG = {
    'LOGIN_ATTEMPTS': 5,
    'LOGIN_WINDOW': 300,  # 5 minutes
    'API_CALLS': 100,
    'API_WINDOW': 3600,  # 1 hour
}

# 2FA Configuration
TWO_FACTOR_ENABLED = os.environ.get('TWO_FACTOR_ENABLED', 'True') == 'True'
OTP_EXPIRY_TIME = int(os.environ.get('OTP_EXPIRY_TIME', 600))  # 10 minutes

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
FILE_UPLOAD_TEMP_DIR = os.path.join(BASE_DIR, 'uploads/temp')
ALLOWED_UPLOAD_EXTENSIONS = ['csv', 'xlsx', 'xls']

# Create logs directory if it doesn't exist
os.makedirs(os.path.join(BASE_DIR, 'logs'), exist_ok=True)
os.makedirs(FILE_UPLOAD_TEMP_DIR, exist_ok=True)
