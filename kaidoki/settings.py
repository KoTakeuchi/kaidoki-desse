import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import logging


# --- ここで確実に .env を読み込む ---
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# ===== 基本設定 =====
SECRET_KEY = os.getenv("SECRET_KEY", "dummy-secret-key")
DEBUG = True
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# 環境フラグ（dev/prod）
ENV = os.getenv("ENV", "dev").lower()   # dev / prod

# ===== DB =====
if ENV == "prod":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306"),
            "OPTIONS": {"charset": "utf8mb4"},
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ===== アプリ =====
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",  # ← これを追加
    "django_bootstrap5",
    "corsheaders",
    "rest_framework",
    "drf_spectacular",
    "main",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # ✅ process_exceptionが確実に呼ばれるよう最後に置く
    # "main.middleware.ErrorLoggingMiddleware",
]

ROOT_URLCONF = "kaidoki.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # ← 共通テンプレートだけ指定
        "APP_DIRS": True,  # ← 各アプリ(main等)配下は自動探索
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "main.context_processors.unread_count",
            ],
        },
    },
]

WSGI_APPLICATION = "kaidoki.wsgi.application"

# ===== 国際化 =====
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "ja")
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Tokyo")
USE_I18N = True
USE_TZ = True

# ===== 静的ファイル =====
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [
    BASE_DIR / "main" / "static",
]
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ===== 認証・遷移 =====
LOGIN_URL = "login"
LOGOUT_REDIRECT_URL = "/main/"
LOGIN_REDIRECT_URL = "main:index"

# ===== メール =====
if ENV == "dev":
    # 開発環境ではコンソールに出力
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    DEFAULT_FROM_EMAIL = 'no-reply@kaidoki-desse.local'
else:
    # 本番環境ではSMTP経由で送信
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.gmail.com"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.getenv("GMAIL_USER")
    EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")
    DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# ===== DRF / OpenAPI =====
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Kaidoki-Desse API",
    "DESCRIPTION": "価格追跡・買い時通知 API",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SERVE_PERMISSIONS": ["rest_framework.permissions.AllowAny"],
    "SWAGGER_UI_SETTINGS": {"deepLinking": True, "persistAuthorization": True},
    "SECURITY": [{"BearerAuth": []}],
    "SECURITY_DEFINITIONS": {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ===== CORS =====
if ENV == "dev":
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOW_ALL_ORIGINS = False
    CORS_ALLOWED_ORIGINS = [
        o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
    ]

# =============================
# メール通知設定（エラー報告用）
# =============================

# ✅ 通常メール設定を上書きせず、明示的に運用通知先を指定
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "3rd.takeuchii@gmail.com")

# ✅ 共通：Gmail送信用のベース設定
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("GMAIL_USER", ADMIN_EMAIL)
EMAIL_HOST_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER


# ✅ 開発環境では「コンソール出力 or 実メール送信」を選べるよう分岐
if ENV == "dev":
    USE_REAL_MAIL = os.getenv("USE_REAL_MAIL", "false").lower() == "true"
    if USE_REAL_MAIL:
        EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
        print("[settings] 📧 実メール送信モード（Gmail）で起動")
    else:
        EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
        print("[settings] 💬 コンソール出力モードで起動")
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    print("[settings] 📧 本番SMTPモードで起動")


# =============================
# 楽天API
# =============================

RAKUTEN_APP_ID = os.getenv("RAKUTEN_APP_ID", "1016082687225252652")
RAKUTEN_BASE_URL = os.getenv(
    "RAKUTEN_BASE_URL", "https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601")


# --- 認証後のリダイレクト先を専用ビューに統一 ---
LOGIN_REDIRECT_URL = "/main/after_login/"

# （任意）ログアウト後の遷移
LOGOUT_REDIRECT_URL = "/main/index/"
