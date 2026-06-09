# Despliegue de Athena

Athena es **una sola app Django** que sirve la web pública (`/`) y el Panel del
Rector (`/admin/`) en el mismo proceso, contra **Oracle Autonomous Database** y
**OCI Object Storage**. No se separa en dos deploys ni va en Netlify/Vercel
(esos no ejecutan Django). Necesita un host que corra Python: contenedor Docker
(OCI Compute / VPS) o una plataforma tipo Railway / Render.

El repo ya queda listo: `Dockerfile`, `Procfile`, WhiteNoise para estáticos y
`settings.py` 100% por variables de entorno.

## Variables de entorno (producción)

| Variable | Para qué |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta de Django (obligatoria). |
| `DJANGO_DEBUG` | `False` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Dominios, separados por coma. Ej.: `panel.tucolegio.edu.co`. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | URLs con esquema. Ej.: `https://panel.tucolegio.edu.co`. |
| `DB_ENGINE` | `oracle` para usar la ADB. |
| `ORACLE_DSN` / `ORACLE_USER` / `ORACLE_PASSWORD` | Conexión a la ADB. |
| `TNS_ADMIN` | Carpeta del wallet ya descomprimido (montada en el host). |
| `ORACLE_WALLET_PASSWORD` | Si el wallet lo requiere. |
| `STORAGE_BACKEND` | `oci` para guardar archivos en el bucket. |
| (credenciales OCI) | Según `almacenamiento/oci_storage.py` / `.env.example`. |

Los secretos y el **wallet de Oracle** se inyectan en tiempo de ejecución
(variables de entorno + volumen montado). **Nunca** van dentro de la imagen ni
del repo (ya están en `.gitignore` / `.dockerignore`).

## Opción A — Docker (OCI Compute / VPS)

```bash
# 1. Construir
docker build -t athena .

# 2. Migrar (una vez)
docker run --rm --env-file .env.prod -v /ruta/al/wallet:/wallet athena \
  python manage.py migrate --noinput

# 3. Crear el superusuario rector (una vez)
docker run --rm -it --env-file .env.prod -v /ruta/al/wallet:/wallet athena \
  python manage.py createsuperuser

# 4. Ejecutar
docker run -d --name athena -p 80:8000 --env-file .env.prod \
  -v /ruta/al/wallet:/wallet --restart unless-stopped athena
```

Pon un proxy (nginx/Caddy) o el balanceador de OCI delante para HTTPS, o usa
Caddy para certificados automáticos. En `.env.prod` define `TNS_ADMIN=/wallet`.

## Opción B — Railway / Render

1. Conecta el repo de GitHub.
2. Define las variables de entorno de la tabla.
3. Sube el wallet como *secret file* y apunta `TNS_ADMIN` a su ruta.
4. La plataforma usa el `Procfile`: corre `migrate` y arranca gunicorn.

## Checklist de producción

- [ ] `DJANGO_DEBUG=False` y `DJANGO_SECRET_KEY` fuerte y único.
- [ ] `DJANGO_ALLOWED_HOSTS` y `DJANGO_CSRF_TRUSTED_ORIGINS` con el dominio real.
- [ ] HTTPS delante (el `settings.py` activa SSL-redirect, cookies seguras y HSTS con `DEBUG=False`).
- [ ] `migrate` aplicado contra la ADB.
- [ ] Superusuario `rector` creado.
- [ ] Bucket OCI con permisos correctos (`STORAGE_BACKEND=oci`).
