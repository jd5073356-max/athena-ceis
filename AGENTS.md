# Guía de Desarrollo de Athena — Mente Colmena (.hive)

Este archivo sirve como el **CLAUDE.md / AGENTS.md** para todas las herramientas de IA (OpenCode, Codex, Copilot, Antigravity, etc.) que trabajen en este repositorio.

---

## 🚨 ESTADO DE ALERTA: ASUNCIÓN DE LIDERAZGO
**Claude Code dejó de funcionar en el entorno local de Juan David.**
**Hermes Agent (hermes-agent)** asume el liderazgo del desarrollo, codificación (Django, HTML, CSS, JavaScript, GSAP, Lenis) y la generación de multimedia (Vertex AI). Todas las IAs secundarias que entren a este repositorio deben alinearse con las decisiones de Hermes Agent y respetar el estado actual documentado aquí.

---

## 📌 Visión del Proyecto
**Athena** es el portal escolar oficial + CMS para la **I.E.D. Complejo Educativo Integral Sopó (CEIS)**.
* **Marca:** Exclusivamente **Código-Beta**. Está terminantemente prohibido utilizar o mencionar "AETHON Industries".
* **Estilo Visual:**
  * **Web Pública:** Diseño editorial de alta gama. Slider Hero con efecto Ken Burns (transiciones CSS aceleradas por GPU, crossfade sin javascript de terceros), cristal traslúcido (glassmorphism), tipografía premium Serif **Lora** para encabezados institucionales y Sans-Serif **Outfit** para la interfaz.
  * **Panel del Rector:** Diseñado con el estilo de una aplicación SaaS moderna en modo oscuro, usando una paleta Slate y Teal, barra lateral de navegación izquierda de alta gama, y tipografías Outfit y Lora.
* **Logotipos:** Los archivos SVG originales `athena_largo.svg` y `athena_isotipo_limpio.svg` en static han sido modificados programáticamente para eliminar los rectángulos y fondos claros, preservando únicamente la versión azul/dorada oscura optimizada para fondos oscuros.

---

## 🛠️ Tecnologías y Configuración del Entorno
* **Framework:** Django 5.2 (Python 3.14.5).
* **Base de Datos:** Oracle Autonomous DB (`django.db.backends.oracle`), esquema `athena_high` en producción. En local se usa fallback para desarrollo.
* **Almacenamiento:** Oracle Cloud Object Storage (`almacenamiento.oci_storage.AlmacenamientoObjectStorage`), bucket público `athena-archivos` (namespace axsqkomilnv5).
* **Servidor Local Activo:** El servidor de desarrollo de Django está corriendo en el fondo en `http://127.0.0.1:8000/` (vía `.venv/bin/python manage.py runserver 0.0.0.0:8000`).

---

## 🗄️ Esquema de Base de Datos (core/models.py)
Jerarquía rígida de guías de estudio:
`AÑO (Anio) ➔ PERÍODO (Periodo, 1-4) ➔ CURSO (Curso) ➔ MATERIA (Materia) ➔ GUÍAS (Guia)`

Contenidos independientes:
* **Noticia:** Anuncios/noticias del colegio.
* **Video:** Enlaces de YouTube (convertidos automáticamente a URLs de embed).
* **Seccion:** Textos editables (home, El Colegio, Proyectos).
* **Imagen:** Fotos de la galería.

---

## 🟢 Estado Actual del Desarrollo
1. **Prioridad de Carga & Custom AdminSite:** En `config/settings.py`, se utiliza la configuración `"panel_rector.apps.AthenaAdminConfig"` para reemplazar el admin por defecto de Django con `"AthenaAdminSite"` (ubicado desacoplado en `panel_rector/admin_site.py`). Esto permite agrupar los modelos de forma elegante en las secciones personalizadas **"ADMINISTRACIÓN CENTRAL"** (Grupos, Usuarios) y **"NÚCLEO (DATOS DEL COLEGIO)"** (Años, Períodos, Cursos, Materias, Guías, Imágenes, Noticias, Secciones, Videos) tanto en el sidebar como en el index.
2. **Logos de Identidad sin Fondo:** Se incorporaron los logos transparentes desde `/home/juan/Descargas/nuevos logos /` hacia `static/logos/`. En la página de login, se ocultaron los elementos por defecto y se configuró para mostrar únicamente un único logo `logo_identidad_oscuro.png` perfectamente centrado sin duplicaciones, mientras que el resto del panel de administración utiliza la versión de 64px de alto del búho azul espacial `athena_isotipo_limpio.svg` con sombras de neón azul y subtítulos estilizados.
3. **Fondo Bokeh CSS y Chips de Acción:** Se enriqueció la base visual con un fondo de luces bokeh fluido mediante gradientes radiales compuestos de CSS nativo. Los enlaces tradicionales de "Añadir" y "Modificar" se rediseñaron por completo como elegantes botones/chips redondeados de estética SaaS empresarial de primer nivel.
4. **Seeding Completo:** Se cargaron las 18 secciones institucionales verbatim reales desde el sitio Wix oficial (9 en "El Colegio" y 9 en "Proyectos") mediante `python manage.py seed_iedceis`.
5. **Credenciales locales de prueba:**
   * **Superadministrador:** Usuario `rector` / Email `iedceis@gmail.com` / Contraseña: **NO se versiona** — créala con `python manage.py createsuperuser` o guárdala en tu gestor de secretos. (Nunca poner contraseñas reales en el repo.)
6. **Validación:** El sistema cuenta con validaciones estrictas de extensión y firma binaria para subida de guías PDF e imágenes de galería.

---

## 🚀 Cómo Continuar el Trabajo (Instrucciones para OpenCode)
* **Web Pública:** http://127.0.0.1:8000/
* **Panel de Administración (SaaS oscuro):** http://127.0.0.1:8000/admin/
* **Siguientes pasos:**
  * Apoyar al rector Juan Carlos Aguirre en la carga de archivos PDF reales para las guías de estudio en el panel.
  * Realizar ajustes de campos finos y validaciones de formularios en el Django Admin según feedback del rector.
  * No modificar la prioridad de `INSTALLED_APPS` ni alterar el tema oscuro SaaS sin coordinar con Hermes Agent.
