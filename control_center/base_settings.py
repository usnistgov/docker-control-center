import fnmatch
import os
from pathlib import Path
from typing import Dict


def find_yml_files(path) -> Dict:
    matches = {}
    for root, _, filenames in os.walk(path, followlinks=True):
        for _ in set().union(
            fnmatch.filter(filenames, "docker-compose.yml"), fnmatch.filter(filenames, "docker-compose.yaml")
        ):
            key = root.split("/")[-1]
            matches[key] = os.path.join(os.path.join(os.getcwd(), root), _)
    return matches


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEBUG = False

ALLOWED_HOSTS = ["localhost"]

# Information security
SESSION_COOKIE_AGE = 2419200  # 2419200 seconds == 4 weeks
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
CSRF_COOKIE_AGE = None
CSRF_USE_SESSIONS = False

# Turned off to allow http to work
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.admin",
    "control_center.libs.authentication",
    "control_center.libs.custom_tags",
    "control_center.apps.compose_ui",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "control_center.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "control_center.wsgi.application"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Date and time formats
DATETIME_FORMAT = "m/d/Y g:i A"
DATE_FORMAT = "m/d/Y"
TIME_FORMAT = "g:i A"
DATETIME_INPUT_FORMATS = ["%m/%d/%Y %I:%M %p"]
DATE_INPUT_FORMATS = ["%m/%d/%Y"]
TIME_INPUT_FORMATS = ["%I:%M %p"]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_L10N = False
USE_TZ = True

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] [%(name)s] %(levelname)s %(module)s %(process)d %(thread)d %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "[%(asctime)s] [%(name)s] %(levelname)s %(message)s", "datefmt": "%d/%b/%Y %H:%M:%S"},
    },
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": os.path.join(BASE_DIR, "config/control_center.log"),
            "formatter": "simple",
        },
        "console": {"formatter": "simple", "class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.request": {"level": "WARNING", "handlers": ["console", "file"], "propagate": True},
        "control_center": {"level": "DEBUG", "handlers": ["console", "file"], "propagate": True},
    },
}
# Logging

STATIC_URL = "/static/"
STATIC_ROOT = "/control-center/config/static/"

# There are three options to authenticate users:
#   1) A decoupled "REMOTE_USER" method (such as Kerberos authentication from a reverse proxy)
#   2) LDAP authentication from Control Center itself (using the LDAP_SERVERS setting)
#   3) Django's ModelBackend (default if no backends are specified here)
# AUTHENTICATION_BACKENDS = ["control_center.libs.authentication.backends.LDAPAuthenticationBackend"]
# AUTHENTICATION_BACKENDS = ['control_center.libs.authentication.backends.NginxKerberosAuthorizationHeaderAuthenticationBackend']

# Specify your list of LDAP authentication servers only if you choose to use LDAP authentication
# LDAP_SERVERS = [{"url": "your.ldap.url", "domain": "YOUR_DOMAIN", "certificate": ""}]

# Control Center specific variables
compose_files = find_yml_files(os.path.join(BASE_DIR, "compose"))
YML_PATH = os.getenv("DOCKER_COMPOSE_YML_PATH") or (next(iter(compose_files.values())) if compose_files else None)

COMPOSE_PROJECT = Path(YML_PATH).parent.name if YML_PATH else None
# when set, this will remove the DOCKER_STRIP_CUSTOM_REGISTRY string from container image names
STRIP_CUSTOM_REGISTRY = ""
# when set, disables service container actions to force the use of service actions
DISABLE_SERVICE_CONTAINER_ACTIONS = False
# use compatibility mode for docker-compose
COMPATIBILITY_MODE = False
# enable auto-refresh of pages. set to a number of seconds or False to disable
AUTO_REFRESH = False
# enable use of control-center with a windows host
WINDOWS_HOST = False
# Docker Compose Command to run after service update and rollback (for example reload nginx in nginx service)
# EXTRA_DOCKER_COMPOSE_COMMAND = ["exec", "--detach", "-T", "nginx", "nginx", "-s", "reload"]

# Title for the header and page title
SITE_TITLE = "Docker Control Center"

# Authentication settings
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "login"
LOGIN_TITLE = SITE_TITLE

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": os.path.join(BASE_DIR, "config/control_center.sqlite3")}
}

from config.settings import *
