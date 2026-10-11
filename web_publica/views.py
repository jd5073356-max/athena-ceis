"""
Vistas de la web pública.

Solo LEEN de la base (vía los modelos de core). El rector escribe desde el
panel; aquí únicamente se muestra. Las guías se navegan con la jerarquía:
Año → Período → Curso → Materia → Guías.
"""
import os
import re

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404, render

from core.models import (
    Anio, Curso, Documento, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video,
)

# Secciones que son solo identidad de la home (no tienen página propia).
IDENTIDAD = {"nombre_sitio", "lema", "mision", "vision", "contacto"}
_EXTS_IMG = (".jpg", ".jpeg", ".png", ".webp", ".gif")


def _secciones() -> dict:
    """Devuelve las secciones de texto indexadas por su clave, para usarlas
    cómodamente en las plantillas (ej. secciones.mision)."""
    return {s.clave: s for s in Seccion.objects.all()}


def _imagenes_seccion(clave: str) -> list:
    """Imágenes (registros Imagen, gestionables desde el admin) de una sección.
    Se sirven desde el almacenamiento (GCS en producción)."""
    seccion = Seccion.objects.filter(clave=clave).first()
    return list(seccion.imagenes.all()) if seccion else []


def home(request):
    """Página de inicio: identidad, accesos, noticias y galería institucional."""
    contexto = {
        "secciones": _secciones(),
        "noticias": Noticia.objects.filter(activo=True)[:3],
        "imagenes_inicio": _imagenes_seccion("inicio"),
    }
    return render(request, "web_publica/home.html", contexto)


# --- Navegación de guías ---------------------------------------------------
def guias_anios(request):
    """Paso 1: años académicos activos."""
    return render(request, "web_publica/guias_anios.html", {
        "secciones": _secciones(),
        "anios": Anio.objects.filter(activo=True),
    })


def guias_periodos(request, anio_id):
    """Paso 2: períodos de un año."""
    anio = get_object_or_404(Anio, pk=anio_id, activo=True)
    return render(request, "web_publica/guias_periodos.html", {
        "secciones": _secciones(),
        "anio": anio,
        "periodos": anio.periodos.all(),
    })


def guias_cursos(request, periodo_id):
    """Paso 3: cursos de un período."""
    periodo = get_object_or_404(Periodo, pk=periodo_id, anio__activo=True)
    return render(request, "web_publica/guias_cursos.html", {
        "secciones": _secciones(),
        "periodo": periodo,
        "cursos": periodo.cursos.all(),
    })


def guias_materias(request, curso_id):
    """Paso 4: materias de un curso."""
    curso = get_object_or_404(Curso, pk=curso_id, periodo__anio__activo=True)
    return render(request, "web_publica/guias_materias.html", {
        "secciones": _secciones(),
        "curso": curso,
        "materias": curso.materias.all(),
    })


def guias_lista(request, materia_id):
    """Paso 5: guías (PDF) de una materia."""
    materia = get_object_or_404(Materia, pk=materia_id, curso__periodo__anio__activo=True)
    return render(request, "web_publica/guias_lista.html", {
        "secciones": _secciones(),
        "materia": materia,
        "guias": materia.guias.all(),
    })


# --- Otras secciones públicas ----------------------------------------------
def noticias_lista(request):
    return render(request, "web_publica/noticias.html", {
        "secciones": _secciones(),
        "noticias": Noticia.objects.filter(activo=True),
    })


def noticia_detalle(request, noticia_id):
    noticia = get_object_or_404(Noticia, pk=noticia_id, activo=True)
    return render(request, "web_publica/noticia_detalle.html", {
        "secciones": _secciones(),
        "noticia": noticia,
    })


def galeria(request):
    return render(request, "web_publica/galeria.html", {
        "secciones": _secciones(),
        "imagenes": Imagen.objects.all(),
    })


def videos(request):
    return render(request, "web_publica/videos.html", {
        "secciones": _secciones(),
        "videos": Video.objects.all(),
    })


# --- Páginas institucionales y proyectos -----------------------------------
def _con_thumb(qs):
    """Adjunta a cada sección la URL de su primera imagen (para la miniatura)."""
    paginas = []
    for s in qs:
        primera = s.imagenes.first()
        s.thumb = primera.archivo.url if primera else None
        paginas.append(s)
    return paginas


def colegio(request):
    """Listado del submenú 'Nosotros' (páginas institucionales)."""
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Nosotros",
        "paginas": _con_thumb(Seccion.objects.filter(categoria=Seccion.Categoria.COLEGIO)),
    })


def proyectos(request):
    """Listado del submenú 'Nuestros Proyectos'."""
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Nuestros Proyectos",
        "paginas": _con_thumb(Seccion.objects.filter(categoria=Seccion.Categoria.PROYECTO)),
    })


def pagina_detalle(request, clave):
    """Detalle de una sección (Nosotros, Proyectos, Circulares, Pre-Matrícula):
    texto verbatim del colegio + galería de sus imágenes reales del Wix."""
    if clave in IDENTIDAD:
        raise Http404("Sección no pública")
    pagina = get_object_or_404(Seccion, clave=clave)
    return render(request, "web_publica/pagina_detalle.html", {
        "secciones": _secciones(),
        "pagina": pagina,
        "imagenes_seccion": _imagenes_seccion(clave),
    })


# --- Circulares, Cronograma y Guías: documentos gestionados desde el admin --
_CAT_ORDEN = ["guia", "circular", "cronograma", "horario", "formato", "manual", "otro"]
_NIVEL_ORDEN = ["bachillerato", "primaria", "preescolar", ""]
_GRADO_ORDEN = ["Prejardín", "PREJARDIN", "Jardín", "JARDIN", "Transición 0º", "Transición", "1º", "2º", "3º", "4º", "5º", "6°", "7°", "8°", "9°", "10°", "11°"]
_PERIODO_ORDEN = ["I", "II", "III", "IV", ""]
_AREA_ORDEN = [
    "Comunicaciones", "Inglés", "Pensamiento Matemático", "Pensamiento Científico",
    "Pensamiento Social", "Pensamiento Artístico", "Pensamiento Ético y Ciudadano",
    "Pensamiento Tecnológico", "Cultura Física y Deportiva",
]


def _obtener_curso(d):
    """Extrae el curso/grado normalizado (ej. 6°, 7°, 1º, Transición)."""
    if d.grado:
        g = d.grado.strip()
        if "TRANS" in g.upper():
            return "Transición"
        return g
    match = re.search(r'\b(1[0-1]|[6-9])[\s°º\.]*', d.titulo)
    if match:
        return f"{match.group(1)}°"
    return "General"


def _guias_jerarquia(items):
    """Estructura las guías: Año → Nivel → Curso → Materia → Guía."""
    nivel_label = dict(Documento.Nivel.choices)
    area_key = lambda a: (_AREA_ORDEN.index(a) if a in _AREA_ORDEN else len(_AREA_ORDEN), a)
    curso_key = lambda c: (_GRADO_ORDEN.index(c) if c in _GRADO_ORDEN else len(_GRADO_ORDEN), c)

    anios = []
    for anio in sorted({d.anio for d in items}, key=lambda x: (x is None, -(x or 0))):
        d_anio = [d for d in items if d.anio == anio]
        niveles = []
        tot_anio = 0
        for niv in _NIVEL_ORDEN:
            d_niv = [d for d in d_anio if (d.nivel or "") == niv]
            if not d_niv:
                continue
            cursos = []
            tot_niv = 0
            distinct_cursos = sorted({_obtener_curso(d) for d in d_niv}, key=curso_key)
            for cur in distinct_cursos:
                d_cur = [d for d in d_niv if _obtener_curso(d) == cur]
                materias = []
                tot_cur = 0
                for area in sorted({d.area or "" for d in d_cur}, key=area_key):
                    docs = sorted((d for d in d_cur if (d.area or "") == area),
                                  key=lambda d: (_PERIODO_ORDEN.index(d.periodo) if d.periodo in _PERIODO_ORDEN else 99, d.titulo))
                    tot_cur += len(docs)
                    materias.append({"materia": area or "General", "docs": docs, "total_docs": len(docs)})
                tot_niv += tot_cur
                cursos.append({"curso": cur, "materias": materias, "total_docs": tot_cur})
            tot_anio += tot_niv
            niveles.append({"nivel": nivel_label.get(niv, "General"), "cursos": cursos, "total_docs": tot_niv})
        anios.append({"anio": anio or "Sin año", "niveles": niveles, "total_docs": tot_anio})
    return anios


def documentos(request):
    """Hub de Circulares, Cronograma y Guías: muestra los Documentos que el
    rector sube desde el admin (servidos desde GCS). Las guías van jerárquicas
    (Año → Nivel → Período → Área), igual al Drive; el resto, en listas."""
    docs = list(Documento.objects.all())
    etiquetas = dict(Documento.Categoria.choices)
    secciones_doc = []
    for cat in _CAT_ORDEN:
        items = [d for d in docs if d.categoria == cat]
        if not items:
            continue
        if cat == "guia":
            secciones_doc.append({"label": etiquetas[cat], "anios": _guias_jerarquia(items)})
        else:
            docs_ord = sorted(items, key=lambda d: (-(d.anio or 0), d.orden, d.titulo))
            secciones_doc.append({"label": etiquetas[cat], "docs": docs_ord})
    return render(request, "web_publica/documentos.html", {
        "secciones": _secciones(),
        "intro": _secciones().get("circulares_padres"),
        "secciones_doc": secciones_doc,
    })


def documento_visor(request, pk):
    """Vista previa embebida (en la web) de un documento, con botón de descarga."""
    doc = get_object_or_404(Documento, pk=pk)
    nombre = (doc.archivo.name or "").lower()
    return render(request, "web_publica/visor.html", {
        "secciones": _secciones(),
        "nombre": doc.titulo,
        "url": doc.archivo.url,
        "es_pdf": doc.es_pdf,
        "es_imagen": nombre.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")),
    })


# --- Asistente Virtual Athena (Groq AI) --------------------------------------
def _fallback_respuesta(q: str) -> str:
    q = q.lower()
    if any(w in q for w in ["guia", "guías", "circular", "cronograma", "taller"]):
        return "Puedes consultar y descargar las circulares, cronogramas y guías SERC organizadas por año, nivel, grado y materia en el repositorio institucional: <br><a class='athena-msg-link' href='/documentos/'>Ir a Circulares, Cronograma y Guías</a>"
    elif any(w in q for w in ["matricula", "matrícula", "inscripci", "cupo", "2026"]):
        return "El proceso de Pre-Matrícula 2026 se realiza diligenciando la hoja de matrícula y adjuntando en PDF el documento de identidad del estudiante y certificado de afiliación en salud: <br><a class='athena-msg-link' href='/p/pre_matricula_2026/'>Ver detalles de Pre-Matrícula 2026</a>"
    elif any(w in q for w in ["horario", "atencion", "atención", "presencial"]):
        return "La secretaría académica atiende presencialmente en la sede principal (Carrera 10 No. 1-31, Sopó, Cundinamarca) los días <strong>martes, miércoles y jueves</strong> de <strong>8:00 a.m. a 12:00 m.</strong>"
    elif any(w in q for w in ["contacto", "telefono", "teléfono", "whatsapp", "correo", "email", "celular"]):
        return "Canales de atención oficial de la I.E.D. CEIS:<br>• Celular / WhatsApp: <a class='athena-msg-link' href='https://wa.me/573108710141' target='_blank' rel='noopener'>310 871 0141</a><br>• Correo institucional: <a class='athena-msg-link' href='mailto:iedceis@gmail.com'>iedceis@gmail.com</a>"
    elif any(w in q for w in ["proyecto", "serc", "prae", "pileo", "ceisopolis"]):
        return "La institución cuenta con proyectos formativos activos como el Sistema Educativo Relacional (SERC), PRAE ambiental, PILEO y Ceisópolis: <br><a class='athena-msg-link' href='/proyectos/'>Ver Proyectos Institucionales</a>"
    elif any(w in q for w in ["rector", "colegio", "mision", "misión", "vision", "visión", "nosotros"]):
        return "La I.E.D. Complejo Educativo Integral Sopó (CEIS) es dirigida por el Lic. Juan Carlos Aguirre Nieto bajo el lema Paz, Educación y Progreso: <br><a class='athena-msg-link' href='/colegio/'>Conocer más sobre el colegio</a>"
    return "Para brindarte información precisa sobre esa solicitud particular o trámites de constancias, por favor contacta a secretaría académica al celular <strong>310 871 0141</strong> o al correo <a class='athena-msg-link' href='mailto:iedceis@gmail.com'>iedceis@gmail.com</a>."


def _fallback_admin_respuesta(q: str) -> str:
    q = q.lower()
    if any(w in q for w in ["guia", "guías", "taller", "material"]):
        return (
            "Para gestionar o subir guías de estudio pedagógicas:<br>"
            "1. Ve a <a class='athena-msg-link' href='/admin/core/guia/add/'>Nueva Guía</a> en el panel.<br>"
            "2. Asigna la materia, curso, período y adjunta el PDF correspondiente.<br>"
            "Consulta el listado completo en el <a class='athena-msg-link' href='/admin/core/guia/'>Repositorio de Guías</a>."
        )
    elif any(w in q for w in ["circular", "documento", "cronograma", "horario", "formato", "manual"]):
        return (
            "Las circulares, cronogramas, formatos y manuales se administran en <strong>Documentos Institucionales</strong>:<br>"
            "Haz clic en <a class='athena-msg-link' href='/admin/core/documento/add/'>Agregar Documento</a> para cargar un nuevo archivo oficial en PDF clasificándolo por año y categoría."
        )
    elif any(w in q for w in ["noticia", "comunicado", "publicar", "boletin", "boletín"]):
        return (
            "Para publicar noticias o comunicados en la página web pública:<br>"
            "Ingresa a <a class='athena-msg-link' href='/admin/core/noticia/add/'>Crear Noticia</a>, diligencia título, texto, fecha y adjunta la imagen destacada."
        )
    elif any(w in q for w in ["color", "colores", "apariencia", "diseño", "paleta", "tema"]):
        return (
            "Puedes personalizar la apariencia y colores de la web pública en tiempo real desde:<br>"
            "<a class='athena-msg-link' href='/admin/core/configuracionapariencia/'>Configuración de Apariencia</a>.<br>"
            "Usa el selector visual de color para cambiar el azul primario, secundario o dorado institucional."
        )
    elif any(w in q for w in ["foto", "imagen", "galeria", "galería"]):
        return (
            "Para agregar fotografías al archivo visual de la institución:<br>"
            "Entra a <a class='athena-msg-link' href='/admin/core/imagen/add/'>Agregar Imagen</a> y selecciona la sección a la que pertenece."
        )
    elif any(w in q for w in ["video", "youtube"]):
        return (
            "Para añadir videos institucionales:<br>"
            "Ingresa a <a class='athena-msg-link' href='/admin/core/video/add/'>Nuevo Video</a> e introduce el título y el enlace o código de YouTube."
        )
    elif any(w in q for w in ["usuario", "clave", "contraseña", "docente", "profesor", "permiso", "rol"]):
        return (
            "La gestión de accesos y permisos se realiza en:<br>"
            "<a class='athena-msg-link' href='/admin/auth/user/'>Usuarios del Sistema</a>. Desde allí puedes crear perfiles de docentes o coordinadores y otorgar permisos."
        )
    elif any(w in q for w in ["curso", "materia", "grado", "año", "periodo", "período"]):
        return (
            "La estructura académica se gestiona mediante la jerarquía:<br>"
            "Años Escolares &rarr; Períodos &rarr; Cursos (1° a 11°) &rarr; Materias.<br>"
            "Puedes revisarla y editarla directamente en el menú lateral del panel."
        )
    return (
        "Estoy a tu disposición para asesorarte en la administración del panel (guías, circulares, noticias, apariencia, usuarios) "
        "y en la redacción formal de comunicaciones institucionales para el colegio."
    )


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json
import urllib.request

@csrf_exempt
@require_POST
def athena_chat_api(request):
    """Endpoint de IA para el asistente Athena conectado a Groq (modo público o asesor admin)."""
    try:
        data = json.loads(request.body.decode("utf-8"))
        mensaje = data.get("mensaje", "").strip()
        contexto = data.get("contexto", "publico").strip().lower()
    except Exception:
        return JsonResponse({"error": "Formato inválido"}, status=400)

    if not mensaje:
        return JsonResponse({"error": "Mensaje requerido"}, status=400)

    es_admin = (contexto == "admin") or (request.user.is_authenticated and request.user.is_staff)

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        fallback = _fallback_admin_respuesta(mensaje) if es_admin else _fallback_respuesta(mensaje)
        return JsonResponse({"respuesta": fallback})

    if es_admin:
        system_prompt = (
            "Eres Athena, la Asesora Oficial y Copiloto de Gestión del Panel del Rector de la "
            "Institución Educativa Departamental Complejo Educativo Integral Sopó (I.E.D. CEIS), ubicada en Sopó, Cundinamarca.\n"
            "Tu misión es asesorar al rector, directivos y administradores en la operación del CMS institucional "
            "y en la gestión escolar directiva (redacción de circulares, directrices académicas, comités, normativa MEN).\n\n"
            "Módulos y Enlaces Directos del Panel de Administración:\n"
            "- Guías Pedagógicas: /admin/core/guia/ (Subir nueva: /admin/core/guia/add/). Permite cargar PDFs didácticos organizados por año, período, curso y materia.\n"
            "- Documentos Institucionales y Circulares: /admin/core/documento/ (Cargar nuevo: /admin/core/documento/add/). Circulares oficiales, cronogramas, formatos de secretaría y manual escolar.\n"
            "- Noticias Institucionales: /admin/core/noticia/ (Nueva noticia: /admin/core/noticia/add/). Publicación con título, fecha, contenido e imagen destacada.\n"
            "- Galería de Imágenes: /admin/core/imagen/ (Subir imagen: /admin/core/imagen/add/). Carga de fotografías por sección (Colegio, Proyectos, Eventos).\n"
            "- Videos Institucionales: /admin/core/video/ (Nuevo video: /admin/core/video/add/). Vinculación de videos mediante enlace o ID de YouTube.\n"
            "- Estructura Académica: /admin/core/anio/, /admin/core/periodo/, /admin/core/curso/, /admin/core/materia/. Configuración de años, períodos, grados (Preescolar a 11°) y materias.\n"
            "- Apariencia y Colores: /admin/core/configuracionapariencia/. Selector interactivo de colores de la web pública (azul, dorado, fondo) en vivo sin tocar código.\n"
            "- Usuarios y Roles: /admin/auth/user/ (Crear usuario: /admin/auth/user/add/). Cuentas de docentes, coordinadores o administradores con permisos de acceso.\n\n"
            "Contexto Institucional:\n"
            "- Rector: Lic. Juan Carlos Aguirre Nieto. Lema: Paz, Educación y Progreso.\n"
            "- Modelo: Sistema Educativo Relacional (SERC), junto con PRAE, PILEO y Ceisópolis.\n"
            "- Puedes redactar borradores formales y diplomáticos de circulares a padres, comunicados internos y actas según normativa educativa colombiana (Decreto 1075 de 2015).\n\n"
            "Reglas de Estilo:\n"
            "1. Responde con tono ejecutivo, formal, respetuoso, conciso y orientador (máximo 2 párrafos cortos).\n"
            "2. NUNCA uses emojis ni símbolos informales.\n"
            "3. Cuando refieras a acciones del panel, incluye el enlace en HTML: ej. <a class='athena-msg-link' href='/admin/core/guia/add/'>Cargar nueva guía</a>.\n"
            "4. Si te piden redactar un texto para circular o comunicado institucional, proporciónalo listo para publicar."
        )
    else:
        system_prompt = (
            "Eres Athena, el asistente virtual institucional de la Institución Educativa Departamental "
            "Complejo Educativo Integral Sopó (I.E.D. CEIS), ubicada en Sopó, Cundinamarca, Colombia.\n"
            "Información Institucional Oficial:\n"
            "- Rector: Lic. Juan Carlos Aguirre Nieto.\n"
            "- Lema: Paz, Educación y Progreso.\n"
            "- Ubicación: Carrera 10 No. 1-31, Sopó, Cundinamarca.\n"
            "- Celular / WhatsApp de secretaría: 310 871 0141.\n"
            "- Correo electrónico: iedceis@gmail.com.\n"
            "- Horario de atención presencial: Martes, miércoles y jueves de 8:00 a.m. a 12:00 m.\n"
            "- Pre-Matrícula 2026: Formulario y requisitos disponibles en /p/pre_matricula_2026/.\n"
            "- Guías escolares y circulares: Repositorio por año, grado y materia disponible en /documentos/.\n"
            "- Proyectos institucionales: SERC (Sistema Educativo Relacional), PRAE, PILEO, Ceisópolis (en /proyectos/).\n"
            "Reglas de Estilo:\n"
            "1. Responde en tono formal, conciso, respetuoso y claro (máximo 1 o 2 párrafos cortos).\n"
            "2. NUNCA uses emojis ni símbolos informales.\n"
            "3. Si refieres a secciones de la web, incluye el enlace en formato HTML: <a class='athena-msg-link' href='/documentos/'>Circulares y Guías</a> o <a class='athena-msg-link' href='/p/pre_matricula_2026/'>Pre-Matrícula 2026</a>.\n"
            "4. Si no sabes un dato específico, remite a la secretaría académica (310 871 0141 o iedceis@gmail.com)."
        )

    payload = {
        "model": "openai/gpt-oss-20b",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": mensaje[:600]},
        ],
        "max_tokens": 350,
        "temperature": 0.3,
    }

    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "AthenaCEIS/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            texto_ia = res["choices"][0]["message"]["content"].strip()
            texto_ia = texto_ia.replace("\n", "<br>")
            return JsonResponse({"respuesta": texto_ia})
    except Exception:
        fallback = _fallback_admin_respuesta(mensaje) if es_admin else _fallback_respuesta(mensaje)
        return JsonResponse({"respuesta": fallback})

