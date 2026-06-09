#!/bin/sh
# Entrypoint de producción (Cloud Run).
# Cloud Run monta un secreto (bundle.tgz) con el wallet de Oracle y la config/llave
# de OCI en /var/secrets/bundle.tgz. Aquí lo desempaquetamos a /secrets y arrancamos.
set -e

if [ -f /var/secrets/bundle.tgz ]; then
  mkdir -p /secrets
  tar xzf /var/secrets/bundle.tgz -C /secrets
fi

exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8080}" --workers 3 --timeout 120
