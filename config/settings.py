import os
import environ
from pathlib import Path
import dj_database_url

# ============================================
# INITIALISATION
# ============================================
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# ============================================
# SECURITY
# ============================================
SECRET_KEY = env('SECRET_KEY', default='django-insecure-dev-key')
DEBUG = env.bool('DEBUG', default=True)

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[
    'localhost',
    '127.0.0.1',
    '.onrender.com',
    'educdim.onrender.com',
])

# ============================================
# DATABASE
# ============================================
DATABASE_URL = env('DATABASE_URL', default=None)

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True
        )
    }
    DATABASES['default']['OPTIONS'] = {
        'connect_timeout': 10,
        'options': '-c statement_timeout=15000ms'
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# ============================================
# SITE INFO
# ============================================
SITE_NAME = env('SITE_NAME', default='EducDim')
SITE_URL = env('SITE_URL', default='https://educdim.onrender.com')

# ============================================
# BREVO (EMAIL)
# ============================================
BREVO_API_KEY = env('BREVO_API_KEY', default='')
BREVO_SENDER_EMAIL = env('BREVO_SENDER_EMAIL', default='noreply@educdim.com')
BREVO_SENDER_NAME = env('BREVO_SENDER_NAME', default='EducDim')

if BREVO_API_KEY:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp-relay.brevo.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = BREVO_SENDER_EMAIL
    EMAIL_HOST_PASSWORD = BREVO_API_KEY
    DEFAULT_FROM_EMAIL = BREVO_SENDER_EMAIL
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    DEFAULT_FROM_EMAIL = 'no-reply@educdim.com'

# ============================================
# TELERIVET (SMS)
# ============================================
TELERIVET_API_KEY = env('TELERIVET_API_KEY', default='')
TELERIVET_PROJECT_ID = env('TELERIVET_PROJECT_ID', default='')

# ============================================
# SECURE SETTINGS
# ============================================
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
else:
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False

# ============================================
# SESSIONS
# ============================================
SESSION_COOKIE_AGE = 3600
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# ============================================
# CSRF
# ============================================
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'

# ============================================
# LANGUAGE & TIMEZONE
# ============================================
LANGUAGE_CODE = 'fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('ht', 'Kreyòl'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
TIME_ZONE = 'America/Port-au-Prince'
USE_I18N = True
USE_TZ = True

# ============================================
# INSTALLED APPS - KOREKTE (RETIRE DOUB sitemaps)
# ============================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',  # ✅ Sèlman sa a, PA mete 'sitemaps' ankò
    'accounts.apps.AccountsConfig',
    'courses.apps.CoursesConfig',
    'enrollments.apps.EnrollmentsConfig',
    'progress.apps.ProgressConfig',
    'quiz.apps.QuizConfig',
    'attendance.apps.AttendanceConfig',
    'badges.apps.BadgesConfig',
    'ranking.apps.RankingConfig',
    'chat.apps.ChatConfig',
    'notifications.apps.NotificationsConfig',
    'theme_manager.apps.ThemeManagerConfig',
    'ads.apps.AdsConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'dashboard.apps.DashboardConfig',
    'todo.apps.TodoConfig',
]

# ============================================
# MIDDLEWARE
# ============================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'theme_manager.middleware.MaintenanceMiddleware',
    'accounts.middleware.UpdateActivityMiddleware',
]

# ============================================
# URLS
# ============================================
ROOT_URLCONF = 'config.urls'

# ============================================
# TEMPLATES
# ============================================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.unread_notifications_count',
                'theme_manager.context_processors.theme_processor',
                'theme_manager.context_processors.breadcrumbs_processor',
                'theme_manager.context_processors.seo_processor',
                'ads.context_processors.banners_processor',
            ],
        },
    },
]

# ============================================
# WSGI
# ============================================
WSGI_APPLICATION = 'config.wsgi.application'

# ============================================
# AUTHENTICATION
# ============================================
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'accounts.validators.ComplexPasswordValidator',
    },
]

AUTH_USER_MODEL = 'accounts.CustomUser'

AUTHENTICATION_BACKENDS = [
    'accounts.backends.UserIDBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:profile'
LOGOUT_REDIRECT_URL = 'accounts:login'

# ============================================
# STATIC & MEDIA
# ============================================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ============================================
# LOGGING
# ============================================
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}
