"""
Configuración de Athena.

Dos modos, ambos controlados por variables de entorno (nunca por código):

- DESARROLLO (por defecto): corre HOY sobre SQLite y guarda los archivos en
  media/. Es el mismo patrón que producción: la base de datos guarda solo la
  RUTA del archivo, no el archivo en sí.
- PRODUCCIÓN: Oracle Autonomous Database (vía python-oracledb) + Oracle Cloud
  Object Storage para los archivos. Se activa con DB_ENGINE=oracle y
  STORAGE_BACKEND=oci. Ver README.md.

Regla de seguridad: NUNCA se ponen secretos en este archivo. Todo lo sensible
llega por variables de entorno (o por el archivo .env, que no se versiona).
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


# --- Carga mínima de .env (sin dependencias externas) ----------------------
def _cargar_env(ruta: Path) -> None:
    """Lee pares CLAVE=VALOR de un archivo .env si existe. No pisa variables
    que ya estén definidas en el entorno real."""
    if not ruta.exists():
        return
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        os.environ.setdefault(clave.strip(), valor.strip().strip('"').strip("'"))


_cargar_env(BASE_DIR / ".env")


def env(clave: str, defecto: str | None = None) -> str | None:
    return os.environ.get(clave, defecto)


def env_bool(clave: str, defecto: bool = False) -> bool:
    return str(env(clave, str(defecto))).lower() in ("1", "true", "yes", "si", "sí", "on")


# --- Seguridad básica ------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", "dev-inseguro-cambiar-en-produccion")
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()]


# --- Aplicaciones ----------------------------------------------------------
INSTALLED_APPS = [
    "panel_rector.apps.PanelRectorConfig",  # personalización del Django Admin (rector)
    "panel_rector.apps.AthenaAdminConfig",  # custom admin site
    "django.contrib.auth",           # login del rector (USUARIOS)
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",                          # modelos compartidos (las 10 tablas)
    "web_publica",                   # sitio público (padres y estudiantes)
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # sirve estáticos en producción
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "web_publica.context_processors.menu_publico",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Base de datos ---------------------------------------------------------
# Django habla con la base de datos según el motor configurado.
_db_engine = env("DB_ENGINE", "sqlite").lower()
if _db_engine in ("postgres", "postgresql", "supabase"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB", env("SUPABASE_DB_NAME", "postgres")),
            "USER": env("POSTGRES_USER", env("SUPABASE_DB_USER", "postgres.peeczetjwxhqominsbzc")),
            "PASSWORD": env("POSTGRES_PASSWORD", env("SUPABASE_DB_PASSWORD", "AthenaPostgres2026!Sec")),
            "HOST": env("POSTGRES_HOST", env("SUPABASE_DB_HOST", "aws-0-sa-east-1.pooler.supabase.com")),
            "PORT": env("POSTGRES_PORT", env("SUPABASE_DB_PORT", "6543")),
        }
    }
elif _db_engine == "oracle":
    # Producción: Oracle Autonomous Database vía python-oracledb.
    _opciones_oracle = {}
    _wallet = env("TNS_ADMIN")
    if _wallet:
        _opciones_oracle["config_dir"] = _wallet
        _opciones_oracle["wallet_location"] = env("ORACLE_WALLET_DIR", _wallet)
    if env("ORACLE_WALLET_PASSWORD"):
        _opciones_oracle["wallet_password"] = env("ORACLE_WALLET_PASSWORD")

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.oracle",
            "NAME": env("ORACLE_DSN"),
            "USER": env("ORACLE_USER"),
            "PASSWORD": env("ORACLE_PASSWORD"),
            "OPTIONS": _opciones_oracle,
        }
    }
else:
    # Desarrollo / Local: SQLite. Cero configuración, corre al instante.
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }



# --- Almacenamiento de archivos (guías PDF, imágenes de galería) -----------
# La base guarda solo la RUTA; el archivo vive aquí.
_STATICFILES = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
_sb = env("STORAGE_BACKEND", "local").lower()
if _sb in ("r2", "s3", "cloudflare"):
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
            "OPTIONS": {
                "bucket_name": env("R2_BUCKET_NAME", "athena"),
                "endpoint_url": env("R2_ENDPOINT_URL", "https://2437c55c10f2f7c1dd8e879e832cd97c.r2.cloudflarestorage.com"),
                "access_key": env("R2_ACCESS_KEY_ID", "02fc89c6dbfe4f40f4a928e05aab975e"),
                "secret_key": env("R2_SECRET_ACCESS_KEY", "4aff049ec9df94700f993e0d62a42892700ec4bcecf94c023e2d25e2607cd144"),
                "region_name": "auto",
                "custom_domain": env("R2_CUSTOM_DOMAIN", "media-athena.maxstudio.lat"),

                "file_overwrite": False,
                "querystring_auth": False,
            },
        },
        "staticfiles": _STATICFILES,
    }
elif _sb == "gcs":

    # Google Cloud Storage. Auth por cuenta de servicio (ADC) — sin API keys.
    # Bucket público de lectura: la web pública ve los archivos por URL directa,
    # y el rector sube imágenes/videos/PDF desde el admin.
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
            "OPTIONS": {
                "bucket_name": env("GS_BUCKET_NAME", "athena-media-ceis"),
                "project_id": env("GS_PROJECT_ID", "gen-lang-client-0454730768"),
                "default_acl": None,        # uniform bucket-level access
                "querystring_auth": False,  # URLs públicas sin firmar
                "file_overwrite": False,
            },
        },
        "staticfiles": _STATICFILES,
    }
elif _sb == "oci":
    STORAGES = {
        "default": {"BACKEND": "almacenamiento.oci_storage.AlmacenamientoObjectStorage"},
        "staticfiles": _STATICFILES,
    }
else:
    STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": _STATICFILES,
    }

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

# Documentos institucionales (guías por año, manual, horarios, circulares...)
# descargados del Drive del colegio. La web los navega y sirve desde aquí.
# En producción se publicarían en Object Storage; configurable por entorno.
DOCS_ROOT = Path(env("DOCS_ROOT", "/home/juan/iedceis_drive"))


# --- Idioma y zona horaria (Colombia, español) -----------------------------
LANGUAGE_CODE = "es-co"
TIME_ZONE = "America/Bogota"
USE_I18N = True
USE_TZ = True


# --- Contraseñas del rector ------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Límite de subida (una guía PDF puede pesar): 25 MB.
DATA_UPLOAD_MAX_MEMORY_SIZE = 26214400
FILE_UPLOAD_MAX_MEMORY_SIZE = 26214400

LOGIN_URL = "/admin/login/"

# Endurecimiento automático cuando DEBUG=False (producción).
if not DEBUG:
    # Cloud Run / balanceadores terminan el TLS y reenvían como HTTP. Sin esto,
    # SECURE_SSL_REDIRECT no detecta el HTTPS real y entra en bucle de redirección.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("DJANGO_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    X_FRAME_OPTIONS = "DENY"
    # En producción WhiteNoise sirve los estáticos comprimidos y versionados (hash de caché).
    STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"
