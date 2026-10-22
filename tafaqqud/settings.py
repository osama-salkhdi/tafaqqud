import os
from pathlib import Path
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.environ.get("DEBUG", "0") == "1"

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
if os.environ.get("RENDER_EXTERNAL_HOSTNAME"):
    ALLOWED_HOSTS.append(os.environ["RENDER_EXTERNAL_HOSTNAME"])
ALLOWED_HOSTS += [h.strip() for h in os.environ.get("EXTRA_HOSTS", "").split(",") if h.strip()]

INSTALLED_APPS = ["attendance"]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.middleware.common.CommonMiddleware",
]
ROOT_URLCONF = "tafaqqud.urls"
WSGI_APPLICATION = "tafaqqud.wsgi.application"
TEMPLATES = []

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}", conn_max_age=600, conn_health_checks=True
    )
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
TIME_ZONE = "Asia/Damascus"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
DATA_UPLOAD_MAX_MEMORY_SIZE = 2 * 1024 * 1024

# إعدادات النظام (تُضبط من Environment في Render)
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")        # رمز دخول المراقبين
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")  # كلمة مرور المسؤول
EXAM_ID = os.environ.get("EXAM_ID", "daraa-2027-stage1")
