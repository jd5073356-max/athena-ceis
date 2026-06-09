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
RUN python manage.py collectstatic --noinput && chmod +x /app/entrypoint.sh

EXPOSE 8080

# El entrypoint desempaqueta el wallet/llaves (montados como secreto) y arranca gunicorn.
# La BD Oracle ADB, el bucket OCI y los secretos llegan por variables de entorno y
# Secret Manager en tiempo de ejecución (nunca se hornean en la imagen).
ENTRYPOINT ["/app/entrypoint.sh"]
