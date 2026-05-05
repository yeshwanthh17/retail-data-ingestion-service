from os import getenv
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]

SECRET_KEY = getenv("DJANGO_SECRET_KEY", "assignment-secret-key")
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "ingestion",
]

MIDDLEWARE = []

ROOT_URLCONF = "config.urls"
TEMPLATES = []
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / getenv("SQLITE_NAME", "data_ingestion.sqlite3"),
    }
}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = False

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

BATCH_SIZE = int(getenv("BATCH_SIZE", "1000"))
