# Athena — imagen de producción (web pública + Panel del Rector, un solo proceso Django).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_DEBUG=False

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Recolecta los estáticos (WhiteNoise los sirve comprimidos y con hash de caché).
RUN python manage.py collectstatic --noinput

EXPOSE 8000

# gunicorn sirve la app. La base Oracle ADB, el bucket OCI y los secretos llegan
# por variables de entorno en tiempo de ejecución (nunca se hornean en la imagen).
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"]
