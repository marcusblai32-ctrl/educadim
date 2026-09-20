import os
from pathlib import Path

import environ
import dj_database_url


# ============================================
# INITIALISATION
# ============================================

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


# ============================================
# SECURITY
# ============================================

SECRET_KEY = env("SECRET_KEY")

DEBUG = env.bool("DEBUG", default=False)

ALLOWED_HOSTS = env.list(
    "ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        ".onrender.com",
        "educadim.onrender.com",
        "educadim.org",
        "www.educadim.org",
    ],
)


# ============================================
# DATABASE
# ============================================

DATABASE_URL = env("DATABASE_URL", default="")

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
            ssl_require=True,
        )
    }

    DATABASES["default"]["OPTIONS"] = {
        "connect_timeout": 10,
        "options": "-c statement_timeout=15000ms",
    }

else:
    if DEBUG:
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / "db.sqlite3",
            }
        }
    else:
        raise RuntimeError(
            "DATABASE_URL is required when DEBUG=False."
        )


# ============================================
# SITE INFO
# ============================================

SITE_NAME = env(
    "SITE_NAME",
    default="EducaDim",
)

SITE_URL = env(
    "SITE_URL",
    default="https://educadim.org",
)


# ============================================
# BREVO (EMAIL)
# ============================================

BREVO_API_KEY = env(
    "BREVO_API_KEY",
    default="",
)

BREVO_SENDER_EMAIL = env(
    "BREVO_SENDER_EMAIL",
    default="noreply@educadim.org",
)

BREVO_SENDER_NAME = env(
    "BREVO_SENDER_NAME",
    default="EducaDim",
)

if BREVO_API_KEY:
    EMAIL_BACKEND = (
        "django.core.mail.backends.smtp.EmailBackend"
    )

    EMAIL_HOST = "smtp-relay.brevo.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True

    EMAIL_HOST_USER = BREVO_SENDER_EMAIL
    EMAIL_HOST_PASSWORD = BREVO_API_KEY

    DEFAULT_FROM_EMAIL = BREVO_SENDER_EMAIL

else:
    EMAIL_BACKEND = (
        "django.core.mail.backends.console.EmailBackend"
    )

    DEFAULT_FROM_EMAIL = "no-reply@educadim.org"


# ============================================
# TELERIVET (SMS)
# ============================================

TELERIVET_API_KEY = env(
    "TELERIVET_API_KEY",
    default="",
)

TELERIVET_PROJECT_ID = env(
    "TELERIVET_PROJECT_ID",
    default="",
)


# ============================================
# CLOUDFLARE R2 (FICHYE MEDIA)
# ============================================

R2_ACCESS_KEY_ID = env(
    "R2_ACCESS_KEY_ID",
    default="",
)

R2_SECRET_ACCESS_KEY = env(
    "R2_SECRET_ACCESS_KEY",
    default="",
)

R2_BUCKET_NAME = env(
    "R2_BUCKET_NAME",
    default="",
)

R2_ACCOUNT_ID = env(
    "R2_ACCOUNT_ID",
    default="",
)

R2_CUSTOM_DOMAIN = env(
    "R2_CUSTOM_DOMAIN",
    default="",
)

# Verifye si R2 configire
R2_ENABLED = all([
    R2_ACCESS_KEY_ID,
    R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME,
    R2_ACCOUNT_ID,
])


# ============================================
# SECURE SETTINGS
# ============================================

if not DEBUG:
    SECURE_SSL_REDIRECT = True

    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_PROXY_SSL_HEADER = (
        "HTTP_X_FORWARDED_PROTO",
        "https",
    )

    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True

    SESSION_COOKIE_SAMESITE = "Lax"
    CSRF_COOKIE_SAMESITE = "Lax"

    SECURE_CONTENT_TYPE_NOSNIFF = True

    X_FRAME_OPTIONS = "DENY"

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

SESSION_COOKIE_SAMESITE = "Lax"


# ============================================
# CSRF
# ============================================

CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"


# ============================================
# LANGUAGE & TIMEZONE
# ============================================

LANGUAGE_CODE = "fr"

LANGUAGES = [
    ("fr", "Français"),
    ("ht", "Kreyòl"),
]

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "America/Port-au-Prince"

USE_I18N = True
USE_TZ = True


# ============================================
# INSTALLED APPS
# ============================================

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sitemaps",

    # ===== R2 STORAGE =====
    "storages",

    "accounts.apps.AccountsConfig",
    "courses.apps.CoursesConfig",
    "enrollments.apps.EnrollmentsConfig",
    "progress.apps.ProgressConfig",
    "quiz.apps.QuizConfig",
    "attendance.apps.AttendanceConfig",
    "badges.apps.BadgesConfig",
    "ranking.apps.RankingConfig",
    "chat.apps.ChatConfig",
    "notifications.apps.NotificationsConfig",
    "theme_manager.apps.ThemeManagerConfig",
    "ads.apps.AdsConfig",
    "subscriptions.apps.SubscriptionsConfig",
    "dashboard.apps.DashboardConfig",
    "todo.apps.TodoConfig",
]


# ============================================
# MIDDLEWARE
# ============================================

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "theme_manager.middleware.MaintenanceMiddleware",
    "accounts.middleware.UpdateActivityMiddleware",
]


# ============================================
# URLS
# ============================================

ROOT_URLCONF = "config.urls"


# ============================================
# TEMPLATES
# ============================================

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "notifications.context_processors.unread_notifications_count",
                "theme_manager.context_processors.theme_processor",
                "theme_manager.context_processors.breadcrumbs_processor",
                "theme_manager.context_processors.seo_processor",
                "ads.context_processors.banners_processor",
            ],
        },
    },
]


# ============================================
# WSGI
# ============================================

WSGI_APPLICATION = "config.wsgi.application"


# ============================================
# AUTHENTICATION
# ============================================

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
        "OPTIONS": {
            "min_length": 8,
        },
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
    {
        "NAME": "accounts.validators.ComplexPasswordValidator",
    },
]


AUTH_USER_MODEL = "accounts.CustomUser"

AUTHENTICATION_BACKENDS = [
    "accounts.backends.UserIDBackend",
    "django.contrib.auth.backends.ModelBackend",
]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "courses:course_list"
LOGOUT_REDIRECT_URL = "accounts:login"


# ============================================
# STATIC FILES
# ============================================

STATIC_URL = "/static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = BASE_DIR / "staticfiles"


# ============================================
# WHITENOISE
# ============================================

WHITENOISE_USE_FINDERS = True

WHITENOISE_AUTOREFRESH = True

WHITENOISE_MANIFEST_STRICT = False


# ============================================
# MEDIA — R2 OUBYEN LOCAL
# ============================================

MEDIA_URL = "/media/"

MEDIA_ROOT = env(
    "MEDIA_ROOT",
    default=str(BASE_DIR / "media"),
)


# ============================================
# STORAGES — KONFIGIRASYON R2
# ============================================

if R2_ENABLED:
    # ===== R2 STORAGE =====
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "access_key": R2_ACCESS_KEY_ID,
                "secret_key": R2_SECRET_ACCESS_KEY,
                "bucket_name": R2_BUCKET_NAME,
                "endpoint_url": f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
                "region_name": "auto",
                "signature_version": "s3v4",
                "default_acl": None,
                "file_overwrite": False,
                "querystring_auth": False,
                "custom_domain": R2_CUSTOM_DOMAIN or None,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }

    # ===== URL PIBLIK POU MEDIA =====
    if R2_CUSTOM_DOMAIN:
        MEDIA_URL = f"https://{R2_CUSTOM_DOMAIN}/"

    # ===== LIMIT MEMWA POU UPLOAD =====
    AWS_S3_FILE_OVERWRITE = False
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=86400",
    }

else:
    # ===== LOCAL STORAGE (DEVLOPMAN) =====
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }


# ============================================
# UPLOAD LIMITS — POU ODDYO/VIDEO
# ============================================

FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50 MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755


# ============================================
# DEFAULT PRIMARY KEY
# ============================================

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ============================================
# LOGGING
# ============================================

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,

    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },

    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
        },

        "django.security": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },

        "utils.notifications": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },

        "storages": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}