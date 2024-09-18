"""
Django settings for BanqueProject project.

Generated by 'django-admin startproject' using Django 5.1.1.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.1/ref/settings/
"""

import os
from pathlib import Path
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-wfvlp!)io$c@c7w@^544t8gj@o(q9odze&swolblgl^nstaz0('

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]


# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'gilchristagbessi92@gmail.com'
EMAIL_HOST_PASSWORD = 'abpw otfh dllf iylw'  # Utilisez le mot de passe d'application ici

DEFAULT_FROM_EMAIL = 'AGBESSI Gilchrist gilchristagbessi92@gmail.com'
SERVER_EMAIL = 'gilchristagbessi92@gmail.com'
NO_REPLY_EMAIL = 'noreply@example.com'

# Pour définir la durée de la session à 7 jours
SESSION_COOKIE_AGE = 7 * 24 * 60 * 60  # 7 jours en secondes

# Paramètres supplémentaires pour l'envoi d'e-mails





# Application definition

INSTALLED_APPS = [
    'modeltranslation',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_bootstrap_email',
    'rosetta',
    'banque_app',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'BanqueProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR,'Templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'BanqueProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/


LANGUAGE_CODE = 'fr'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGES = [
    ('en', _('English')),
    ('fr', _('French')),
    ('es', _('Spanish')),
    ('it', _('Italian')),
]
LOCALE_PATHS = [BASE_DIR / 'locale']

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

STRIPE_SECRET_KEY_TEST = 'sk_test_51KSdusCrWcSq8gbyUhRFKyLQ0kf9yiIMTziQf5wlYDEsfZwVvfqw0UAAl5Q1d5JlHrGuB3Lj5Xld8DSZDdoGjzlv00kmj0vCEd'
PRODUCT_PRICE = 'price_1Pw8MxCrWcSq8gbyl3gz5ndR'
REDIRECT_DOMAIN = 'http://127.0.0.1:8000/' #'http://3.143.168.100:8000/'
STRIPE_WEBHOOK_SECRET_TEST = 'whsec_d06e4ca494d842c0b4f433bd1d621999824684d55d48d9b29debd328a6dcfa01'
STRIPE_PUBLIC_KEY_TEST = "pk_test_51KSdusCrWcSq8gbyrsMCGYGCJXOJw1DyWFyv28duXcwa9aLNo2pifWsuI6UUdU448g52UE9ojPsAbcHjnEf3S8wD00wMTKSpqO"


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}

