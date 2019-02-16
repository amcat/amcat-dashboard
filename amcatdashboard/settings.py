"""
Django settings for amcatdashboard project.

Generated by 'django-admin startproject' using Django 1.8.2.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.8/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
import hashlib
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DJANGO_DEBUG") == "1"

if "DJANGO_SECRET_KEY" not in os.environ and not DEBUG:
    raise ValueError("You must supply DJANGO_SECRET_KEY as environment variable.")


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "default")
CRON_SECRET = hashlib.sha256((SECRET_KEY + "6132600e-47a5-49e6-a3ff-4af22b02cd71").encode()).hexdigest()[:20]


ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")
if DEBUG:
    ALLOWED_HOSTS += ["*"]

STATIC_ROOT = os.path.join(BASE_DIR, "srv")
MEDIA_ROOT = os.path.join(BASE_DIR, "srv/media")

# Application definition
AUTH_USER_MODEL = 'dashboard.User'

LOGIN_EXEMPT_URLS = [
    '^account/.+',
    '^dashboard/token_setup$',
    '^dashboard/amcat',
    '^dashboard/cron-trigger/\w+$'
]

MIGRATION_MODULES = {
    'account': 'amcatdashboard.account_migrations'
}

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get("DASHBOARD_EMAIL_HOST", 'localhost')
    EMAIL_PORT = os.environ.get("DASHBOARD_EMAIL_PORT", 587)
    EMAIL_HOST_USER = os.environ.get("DASHBOARD_EMAIL_USER", '')
    EMAIL_HOST_PASSWORD = os.environ.get("DASHBOARD_EMAIL_PASSWORD", '')
    EMAIL_USE_TLS = os.environ.get("DASHBOARD_EMAIL_TLS", 'Y') in ("1", "Y", "ON")

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.admin',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django_extensions',
    'bootstrapform',
    'account',
    'amcatdashboard',
    'dashboard',
    'pinax_theme_bootstrap',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'dashboard.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'account.middleware.LocaleMiddleware',
    'account.middleware.TimezoneMiddleware',
    'dashboard.middleware.APITokenNeededMiddleware',
    'dashboard.middleware.MethodOverrideMiddleware'
)

STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)

ROOT_URLCONF = 'amcatdashboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ["templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'account.context_processors.account',
                'dashboard.context_preprocessors.dashboard_settings'
            ],
            'builtins': [
                'django.templatetags.i18n'
            ]
        },
    },
]


WSGI_APPLICATION = 'amcatdashboard.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DASHBOARD_DB_NAME", "dashboard"),
        'USER': os.environ.get("DASHBOARD_DB_USER", "dashboard"),
        'PASSWORD': os.environ.get("DASHBOARD_DB_PASSWORD", ""),
        'HOST': os.environ.get("DASHBOARD_DB_HOST", ""),
        'PORT': os.environ.get("DASHBOARD_DB_PORT", "")
    }
}


CACHES = {
    'default': {
        # LocMemCache doesn't share its contents with other processes.
        # Only use default for small things that can be replicated in memory safely.
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'dashboard-cache',
    },

    # FileBasedCache isn't particularly fast, and it is recommended to a configure a different caching backend instead.
    'query': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': 'cache/dashboard/queries',
        'OPTIONS': {
            'eviction_policy': 'least-recently-used'
        }
    },

}

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/

LANGUAGE_CODE = 'en'

gettext_noop = lambda s: s

LANGUAGES = (('en', gettext_noop('English')), ('nl', gettext_noop('Dutch')))

LOCALE_PATHS = (
    'locale',
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/

STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# django-user-accounts
ACCOUNT_EMAIL_UNIQUE = True
ACCOUNT_EMAIL_CONFIRMATION_REQUIRED = True
ACCOUNT_USER_DISPLAY = lambda user: user.email

SESSION_COOKIE_NAME = 'dashboard__sessionid'
CSRF_COOKIE_NAME = 'dashboard__csrftoken'

SESSION_ID = os.environ.get("DJANGO_SESSION_ID")

# Comment this line to fall back to the default theme.
GLOBAL_THEME = "material"

DASHBOARD_ALLOW_MULTIPLE_SYSTEMS = True
