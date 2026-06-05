# Athena

Sitio web escolar con **panel de administración (CMS)** para que el rector
gestione todo el contenido **sin tocar código**. Desarrollado por **Código-Beta
(AETHON Industries)**.

Son dos áreas que comparten la misma base de datos:

- **Web pública** (`/`) — la que ven padres y estudiantes.
- **Panel del Rector** (`/admin/`) — área privada con login; el rector edita todo
  con formularios. Lo que guarda aparece automáticamente en la web pública.

**Stack:** Python · Django · Oracle Autonomous Database (vía `python-oracledb`) ·
Oracle Cloud Object Storage. Idioma: español.

---

## Arquitectura en una línea

```
RECTOR → Panel (Django Admin, login) → Django → Oracle DB (textos, links, RUTAS)
                                            └──→ Object Storage (PDFs, imágenes)
WEB PÚBLICA ← Django lee ← Oracle DB
```

- La base de datos guarda **solo datos y la RUTA** de cada archivo, nunca el
  archivo en sí.
- Los archivos pesados (PDFs, imágenes) viven en **Object Storage**.
- **Django es la única capa** que habla con la base; ni la web ni el panel tocan
  Oracle "a mano".

---

## Estructura

```
athena/
├── config/            Proyecto Django (settings, urls, wsgi)
├── core/              Modelos compartidos (las 10 tablas) + validadores + seed
├── panel_rector/      Panel del Rector (personalización de Django Admin)
├── web_publica/       Sitio público (vistas, urls, plantillas)
├── almacenamiento/    Integración con Oracle Object Storage (backend OCI)
├── base-de-datos/     Esquema Oracle (SQL) + datos de ejemplo
├── manage.py
├── requirements.txt
└── .env.example       Plantilla de variables de entorno (copiar a .env)
```

### Modelo de datos (jerarquía de guías)

```
AÑO → PERÍODO (1–4) → CURSO → MATERIA → GUÍAS
```

Tablas: `ANIOS`, `PERIODOS`, `CURSOS`, `MATERIAS`, `GUIAS`, `NOTICIAS`, `VIDEOS`,
`SECCIONES`, `IMAGENES`. El login del rector (`USUARIOS`) lo gestiona el sistema
de autenticación de Django.

---

## Puesta en marcha — Desarrollo (corre hoy, sin Oracle)

Por defecto usa **SQLite** y guarda archivos en `media/`. Cero configuración de
nube. Mismo patrón que producción (la base guarda solo la ruta del archivo).

```bash
cd athena
python3 -m venv .venv
.venv/bin/pip install Django          # en dev basta Django
# (opcional) cp .env.example .env       y ajusta lo que quieras

.venv/bin/python manage.py migrate     # crea las tablas
.venv/bin/python manage.py seed_demo   # datos de ejemplo (idempotente)
.venv/bin/python manage.py createsuperuser   # crea el usuario del rector
.venv/bin/python manage.py runserver
```

- Web pública: <http://127.0.0.1:8000/>
- Panel del Rector: <http://127.0.0.1:8000/admin/>

> El `seed_demo` carga la jerarquía 2026 → Período 1 → 6°A → Matemáticas → una
> guía PDF, más secciones, una noticia, un video y una imagen, para ver todo
> funcionando de inmediato.

---

## Qué hace el rector (panel)

Entra con su usuario y, con formularios:

1. **Guías** — sube/elimina PDFs por Año → Período → Curso → Materia (al abrir un
   Año aparecen sus Períodos, dentro un Período sus Cursos, etc.).
2. **Imágenes** — sube/elimina imágenes de la galería.
3. **Noticias** — crea, edita y borra anuncios.
4. **Videos** — pega un enlace de YouTube; se embebe solo.
5. **Secciones** — edita los textos de la home (misión, visión, contacto…).

Validación automática: las guías solo aceptan **PDF**; la galería solo **imágenes**
(se verifica extensión y firma binaria).

> **Identidad del colegio** (nombre, logo, colores, fotos): la suministra Juan
> aparte. Los textos se editan en *Secciones* del panel. La marca visual por
> defecto (azul/dorado) es solo un marcador de posición.

---

## Despliegue — Producción (Oracle Free Tier)

### 1. Crear la Oracle Autonomous Database (Free Tier)

1. En Oracle Cloud → *Autonomous Database* → **Create**. Elige *Always Free*.
2. Define la contraseña de `ADMIN`.
3. *Database connection* → **Download wallet** (mTLS). Descomprime el `.zip` en
   una carpeta del servidor (ej. `/opt/athena/wallet`).
4. El alias TNS (ej. `nombreddb_high`) está en el `tnsnames.ora` del wallet.

### 2. Configurar las variables de entorno

Copia `.env.example` a `.env` y ajusta:

```ini
DJANGO_SECRET_KEY=...            # python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=tu-dominio.com

DB_ENGINE=oracle
ORACLE_DSN=nombreddb_high
ORACLE_USER=ADMIN
ORACLE_PASSWORD=...
TNS_ADMIN=/opt/athena/wallet     # carpeta del wallet descomprimido
```

> `TNS_ADMIN` debe estar también en el entorno del proceso (Django lo usa para
> localizar el wallet). `python-oracledb` se conecta en modo *thin*, sin cliente
> Oracle pesado.

### 3. Configurar Object Storage (archivos)

1. Crea un *bucket* en OCI Object Storage (ej. `athena-archivos`).
2. Añade al `.env`:

```ini
STORAGE_BACKEND=oci
OCI_NAMESPACE=...                # Object Storage → namespace del tenancy
OCI_BUCKET=athena-archivos
OCI_REGION=sa-bogota-1
OCI_AUTH=config                  # usa ~/.oci/config; o "instance_principal" en una VM OCI
# Acceso a los archivos desde el navegador (elige uno):
OCI_PUBLIC=true                  # bucket público → URL directa
# OCI_PAR_BASE_URL=https://.../  # o un Pre-Authenticated Request si es privado
```

3. Configura las credenciales OCI: archivo `~/.oci/config` (API key) **o**
   *instance principals* si Django corre en una VM de OCI.

### 4. Instalar y arrancar

```bash
.venv/bin/pip install -r requirements.txt    # incluye oracledb y oci
.venv/bin/python manage.py migrate           # crea las tablas en Oracle
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py createsuperuser
# Servir con gunicorn detrás de Nginx (HTTPS):
.venv/bin/gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

> **Nota sobre el esquema:** en este proyecto la fuente de verdad de las tablas
> es Django (`migrate`). El archivo `base-de-datos/esquema_oracle.sql` documenta
> el esquema equivalente para revisión de un DBA; `datos_ejemplo.sql` es la
> versión SQL de los datos de prueba.

### Plan B para los PDFs (no preferido)

Si al inicio no se puede usar Object Storage, los PDFs pueden guardarse temporal
como BLOB en Oracle. **No es la opción preferida** (infla la base). La meta es
Object Storage. Para activarlo habría que cambiar el `FileField` de `Guia` por un
campo binario; no viene activado.

---

## Seguridad

- El panel exige **login** (un solo administrador: el rector).
- **Nunca** se ponen secretos en el código: todo va por variables de entorno /
  `.env` (que está en `.gitignore`).
- En producción (`DJANGO_DEBUG=false`) se activan cookies seguras, HSTS y
  redirección a HTTPS automáticamente.
- Validación de archivos subidos (PDF / imagen) por extensión y firma binaria.

---

## Comandos útiles

```bash
.venv/bin/python manage.py check          # revisión del proyecto
.venv/bin/python manage.py seed_demo      # recargar datos de ejemplo
.venv/bin/python manage.py createsuperuser
.venv/bin/python manage.py runserver
```
