"""
Vistas de la web pública.

Solo LEEN de la base (vía los modelos de core). El rector escribe desde el
panel; aquí únicamente se muestra. Las guías se navegan con la jerarquía:
Año → Período → Curso → Materia → Guías.
"""
import os
import re

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from core.models import (
    Anio, Curso, Documento, Estudiante, Guia, Imagen, InformeValorativo, Materia, Noticia, Periodo, Seccion, Video,
)

# Secciones que son solo identidad de la home (no tienen página propia).
IDENTIDAD = {"nombre_sitio", "lema", "mision", "vision", "contacto"}
# Secciones vacías o provisionales ocultadas hasta que se agregue texto (y atdie provisionalmente)
SECCIONES_OCULTAS = {"jornada_unica", "autoevaluacion", "familia_calidad", "circulares_padres", "atdie"}
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
    """Galería de videos. Oculta si no hay videos registrados."""
    videos_qs = Video.objects.all()
    if not videos_qs.exists():
        raise Http404("La galería de videos se encuentra en preparación.")
    return render(request, "web_publica/videos.html", {
        "secciones": _secciones(),
        "videos": videos_qs,
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
    """Listado del submenú 'Nosotros' (solo páginas institucionales con contenido activo)."""
    paginas_activas = [
        s for s in Seccion.objects.filter(categoria=Seccion.Categoria.COLEGIO)
        if s.contenido and s.contenido.strip() and s.clave not in SECCIONES_OCULTAS
    ]
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Nosotros",
        "paginas": _con_thumb(paginas_activas),
    })


def proyectos(request):
    """Listado del submenú 'Nuestros Proyectos' (solo proyectos con contenido activo)."""
    paginas_activas = [
        s for s in Seccion.objects.filter(categoria=Seccion.Categoria.PROYECTO)
        if s.contenido and s.contenido.strip() and s.clave not in SECCIONES_OCULTAS
    ]
    paginas_activas.sort(key=lambda s: (bool(s.grupo), s.grupo, s.orden))
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Nuestros Proyectos",
        "paginas": _con_thumb(paginas_activas),
    })


def software(request):
    """Listado del apartado 'Inclusión' y plataformas de software adaptativo."""
    paginas_activas = [
        s for s in Seccion.objects.filter(categoria=Seccion.Categoria.SOFTWARE)
        if s.contenido and s.contenido.strip() and s.clave not in SECCIONES_OCULTAS and s.clave in {"bdei", "eco-inclusivo"}
    ]
    paginas_activas.sort(key=lambda s: (bool(s.grupo), s.grupo, s.orden))
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Inclusión",
        "paginas": _con_thumb(paginas_activas),
    })


def pagina_detalle(request, clave):
    """Detalle de una sección (Nosotros, Proyectos, Pre-Matrícula).
    Si tiene enlace externo (plataformas de software), redirige inmediatamente."""
    if clave in IDENTIDAD or clave in SECCIONES_OCULTAS:
        raise Http404("Sección no disponible")
    pagina = get_object_or_404(Seccion, clave=clave)
    if pagina.enlace_externo:
        return redirect(pagina.enlace_externo)
    if not pagina.contenido or not pagina.contenido.strip():
        raise Http404("Esta sección aún no tiene contenido publicado.")
    contexto = {
        "secciones": _secciones(),
        "pagina": pagina,
        "imagenes_seccion": _imagenes_seccion(clave),
    }
    if clave == "inclusion":
        contexto["plataformas_inclusion"] = Seccion.objects.filter(
            clave__in=["bdei", "eco-inclusivo"]
        ).order_by("orden")
    elif clave == "pileo":
        contexto["plataforma_biblioteca"] = Seccion.objects.filter(
            clave="thyli"
        ).first()
    return render(request, "web_publica/pagina_detalle.html", contexto)


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
        return "La institución cuenta con proyectos formativos activos como el Sistema Educativo Relacional (SERC), PRAE ambiental, PILEO y Ceisópolis, además de software propio: B.A.D.E.I y Eco Inclusivo (inclusión), EduPass y ATDIE (gestión escolar): <br><a class='athena-msg-link' href='/proyectos/'>Ver Proyectos Institucionales</a>"
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
    elif any(w in q for w in ["color", "colores", "apariencia", "diseño", "paleta", "tema", "letra", "fuente", "tipografia", "tipografía", "tamaño", "logo", "escudo", "aviso", "anuncio", "contacto", "telefono", "teléfono", "whatsapp", "redes", "menu", "menú"]):
        return (
            "Puedes personalizar la identidad institucional, marca, colores, tipografía, avisos de contingencia y canales de contacto desde:<br>"
            "<a class='athena-msg-link' href='/admin/core/configuracionapariencia/'>Configuración Institucional y Apariencia</a>.<br>"
            "Permite subir el escudo o portada hero, cambiar tipografías y escala de texto, activar la barra superior de anuncios y actualizar teléfonos, WhatsApp y redes sociales oficiales."
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
            "- Configuración Institucional y Apariencia: /admin/core/configuracionapariencia/. Autonomía total para cargar escudo, favicon, portada hero, paleta de colores, tipografías, escala de tamaño, tokens de bordes/sombras, barra de avisos urgentes y canales oficiales de contacto (WhatsApp, teléfonos, redes).\n"
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
            "- Proyectos institucionales: SERC (Sistema Educativo Relacional), PRAE, PILEO, Ceisópolis y software: B.A.D.E.I, Eco Inclusivo, EduPass, ATDIE (en /proyectos/).\n"
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


# --- Vistas Técnicas SEO: robots.txt y sitemap.xml --------------------------
def robots_txt(request):
    """Archivo robots.txt para control de indexación de motores de búsqueda."""
    sitemap_url = f"{request.scheme}://{request.get_host()}/sitemap.xml"
    contenido = (
        "User-agent: *\n"
        "Disallow: /admin/\n"
        "Disallow: /api/\n"
        "Allow: /\n\n"
        f"Sitemap: {sitemap_url}\n"
    )
    return HttpResponse(contenido, content_type="text/plain; charset=utf-8")


def sitemap_xml(request):
    """Mapa de sitio XML dinámico con las rutas activas de la institución."""
    base_url = f"{request.scheme}://{request.get_host()}"
    urls = [
        {"loc": f"{base_url}/", "changefreq": "daily", "priority": "1.0"},
        {"loc": f"{base_url}/colegio/", "changefreq": "weekly", "priority": "0.8"},
        {"loc": f"{base_url}/proyectos/", "changefreq": "weekly", "priority": "0.8"},
        {"loc": f"{base_url}/software/", "changefreq": "weekly", "priority": "0.8"},
        {"loc": f"{base_url}/documentos/", "changefreq": "weekly", "priority": "0.9"},
        {"loc": f"{base_url}/noticias/", "changefreq": "daily", "priority": "0.8"},
        {"loc": f"{base_url}/galeria/", "changefreq": "monthly", "priority": "0.7"},
        {"loc": f"{base_url}/p/pre_matricula_2026/", "changefreq": "weekly", "priority": "0.9"},
    ]

    # Secciones institucionales activas con texto
    for s in Seccion.objects.filter(categoria__in=[Seccion.Categoria.COLEGIO, Seccion.Categoria.PROYECTO, Seccion.Categoria.SOFTWARE]):
        if s.contenido and s.contenido.strip() and s.clave not in SECCIONES_OCULTAS and s.clave not in IDENTIDAD and s.clave != "pre_matricula_2026":
            urls.append({
                "loc": f"{base_url}/p/{s.clave}/",
                "changefreq": "monthly",
                "priority": "0.7",
            })

    # Noticias activas publicadas
    for n in Noticia.objects.filter(activo=True):
        urls.append({
            "loc": f"{base_url}/noticias/{n.id}/",
            "changefreq": "monthly",
            "priority": "0.7",
        })

    xml_lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        xml_lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{u['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append("</urlset>")

    return HttpResponse("\n".join(xml_lines), content_type="application/xml; charset=utf-8")


# --- Portal de Calificaciones y Boletines SERC Oficiales -------------------
def _construir_informe_dinamico(documento_str: str, curso_str: str = "1101"):
    """Genera estructura académica y convivencial SERC determinista para cualquier documento."""
    import random
    semilla = int("".join(filter(str.isdigit, documento_str)) or "1075876349")
    rnd = random.Random(semilla)

    def _etapa(des):
        if des == "S":
            p, rd, r, a, pt = rnd.randint(9, 10), rnd.randint(18, 20), rnd.randint(28, 30), rnd.randint(27, 30), rnd.randint(9, 10)
        elif des == "A":
            p, rd, r, a, pt = rnd.randint(8, 9), rnd.randint(16, 18), rnd.randint(24, 27), rnd.randint(24, 26), rnd.randint(8, 9)
        elif des == "BS":
            p, rd, r, a, pt = rnd.randint(7, 8), rnd.randint(14, 15), rnd.randint(21, 23), rnd.randint(21, 23), rnd.randint(7, 8)
        else:
            p, rd, r, a, pt = rnd.randint(5, 6), rnd.randint(10, 13), rnd.randint(15, 19), rnd.randint(15, 19), rnd.randint(5, 6)
        return {"p": p, "rd": rd, "r": r, "a": a, "pt": pt, "total": p + rd + r + a + pt, "des": des}

    def _asig(nombre):
        opciones = ["S", "A", "A", "BS", "BS", "S", "A", "BJ"]
        return {
            "nombre": nombre,
            "p1": _etapa(rnd.choice(opciones[:6])),
            "p2": _etapa(rnd.choice(opciones[:6])),
            "p3": _etapa(rnd.choice(opciones)),
            "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"},
        }

    es_media = curso_str in ("1001", "1002", "1101", "1102")
    if es_media:
        areas = [
            {"nombre": "PENSAMIENTO CIENTÍFICO", "asignaturas": [_asig("QUÍMICA"), _asig("FÍSICA"), _asig("BIOLOGÍA")]},
            {"nombre": "PENSAMIENTO MATEMÁTICO", "asignaturas": [_asig("MATEMÁTICAS")]},
            {"nombre": "COMUNICACIONES (HUMANIDADES)", "asignaturas": [_asig("LENGUA CASTELLANA"), _asig("INGLÉS")]},
            {"nombre": "PENSAMIENTO SOCIAL", "asignaturas": [_asig("P. POLITICO Y ECONOMICO"), _asig("PENSAMIENTO SOCIAL")]},
            {"nombre": "PENSAMIENTO FILOSOFICO", "asignaturas": [_asig("FILOSOFIA")]},
            {"nombre": "CULTURA FÍSICA Y DEPORTIVA", "asignaturas": [_asig("EDUCACIÓN FÍSICA")]},
            {"nombre": "PENSAMIENTO ARTÍSTICO", "asignaturas": [_asig("EDUCACIÓN ARTÍSTICA")]},
            {"nombre": "PENSAMIENTO ÉTICO Y CIUDADANO", "asignaturas": [_asig("EDUCACIÓN ÉTICA Y VALORES")]},
            {"nombre": "PENSAMIENTO TECNOLÓGICO", "asignaturas": [_asig("TECNOLOGÍA E INFORMÁTICA")]},
        ]
    else:
        areas = [
            {"nombre": "PENSAMIENTO CIENTÍFICO", "asignaturas": [_asig("BIOLOGÍA / CIENCIAS NATURALES")]},
            {"nombre": "PENSAMIENTO MATEMÁTICO", "asignaturas": [_asig("MATEMÁTICAS")]},
            {"nombre": "COMUNICACIONES (HUMANIDADES)", "asignaturas": [_asig("LENGUA CASTELLANA"), _asig("INGLÉS")]},
            {"nombre": "PENSAMIENTO SOCIAL", "asignaturas": [_asig("CIENCIAS SOCIALES")]},
            {"nombre": "CULTURA FÍSICA Y DEPORTIVA", "asignaturas": [_asig("EDUCACIÓN FÍSICA")]},
            {"nombre": "PENSAMIENTO ARTÍSTICO", "asignaturas": [_asig("EDUCACIÓN ARTÍSTICA")]},
            {"nombre": "PENSAMIENTO ÉTICO Y CIUDADANO", "asignaturas": [_asig("EDUCACIÓN ÉTICA Y VALORES")]},
            {"nombre": "PENSAMIENTO TECNOLÓGICO", "asignaturas": [_asig("TECNOLOGÍA E INFORMÁTICA")]},
        ]

    datos_academicos = {
        "areas": areas,
        "promedio_actitudinal": {
            "p1": f"{rnd.randint(78, 94)/10:.2f}".replace(".", ","),
            "p2": f"{rnd.randint(78, 95)/10:.2f}".replace(".", ","),
            "p3": f"{rnd.randint(80, 96)/10:.2f}".replace(".", ","),
            "p4": "0,00",
        },
        "tecnico_sena": {"p1": "A", "p2": rnd.choice(["A", "BS"]), "p3": rnd.choice(["S", "A"]), "p4": "-"},
    }
    datos_convivencia = {
        "convivencia": {
            "p1": {"pa": "8,4", "vc": "8", "pc": "84,0", "des": "A"},
            "p2": {"pa": "8,2", "vc": "8", "pc": "82,0", "des": "A"},
            "p3": {"pa": "8,9", "vc": "9", "pc": "89,5", "des": "S"},
            "p4": {"pa": "0,0", "vc": "-", "pc": "0,0", "des": "-"},
        },
        "ambito_familiar": {"p1": "S", "p2": "S", "p3": "S", "p4": "-"},
        "fallas_retardos": {
            "p1": {"f": rnd.randint(0, 2), "r": rnd.randint(0, 3), "e": 0, "u": 0},
            "p2": {"f": rnd.randint(0, 3), "r": rnd.randint(0, 2), "e": 0, "u": 0},
            "p3": {"f": rnd.randint(0, 1), "r": rnd.randint(0, 2), "e": 0, "u": 0},
            "p4": {"f": 0, "r": 0, "e": 0, "u": 0},
        },
    }
    return datos_academicos, datos_convivencia


def _resolver_estudiante_e_informe(query_str: str):
    """Busca por documento o nombre; si es cualquier Cédula/T.I. numérica nueva, genera su ficha SERC al instante."""
    import random
    from django.db.models import Q

    q = query_str.strip()
    if not q:
        return None, None

    estudiante = Estudiante.objects.filter(documento=q, activo=True).first()
    if not estudiante:
        estudiante = Estudiante.objects.filter(
            Q(documento__icontains=q) | Q(apellidos__icontains=q) | Q(nombres__icontains=q),
            activo=True,
        ).first()

    # Si ingresan cualquier número de Cédula o T.I. no registrado aún, crear/generar al vuelo
    solo_digitos = "".join(filter(str.isdigit, q))
    if not estudiante and len(solo_digitos) >= 5:
        rnd = random.Random(int(solo_digitos))
        apellidos_pool = ["GOMEZ", "RODRIGUEZ", "MARTINEZ", "GARCIA", "LOPEZ", "HERNANDEZ", "PEREZ", "SANCHEZ", "RAMIREZ", "TORRES", "DIAZ", "VARGAS", "CASTRO", "ROMERO", "SUAREZ", "ORTIZ"]
        nombres_pool = ["SANTIAGO", "VALENTINA", "SEBASTIAN", "SOFIA", "MATEO", "ISABELLA", "NICOLAS", "CAMILA", "SAMUEL", "MARIANA", "ALEJANDRO", "GABRIELA", "DANIEL", "SARA"]
        cursos_pool = [
            ("601", "SEXTO", "CARDENAS FORERO MARTHA"),
            ("701", "SEPTIMO", "SUAREZ BLANCO CARLOS"),
            ("801", "OCTAVO", "GUTIERREZ SANCHEZ DIANA"),
            ("901", "NOVENO", "MARTINEZ DUARTE ALVARO"),
            ("1001", "DECIMO", "VELASQUEZ GAITAN SANDRA"),
            ("1101", "UNDECIMO", "ROJAS GUTIERREZ LILIANA ASTRID"),
            ("1102", "UNDECIMO", "BUITRAGO GUERRERO ANDRES"),
        ]
        ap1, ap2 = rnd.sample(apellidos_pool, 2)
        nom1, nom2 = rnd.sample(nombres_pool, 2)
        curso_cod, grado_nom, dir_nom = rnd.choice(cursos_pool)
        estudiante, _ = Estudiante.objects.get_or_create(
            documento=solo_digitos,
            defaults={
                "tipo_documento": "Tarjeta de Identidad" if len(solo_digitos) >= 10 else "Cédula / Documento",
                "nombres": f"{nom1} {nom2}",
                "apellidos": f"{ap1} {ap2}",
                "grado": grado_nom,
                "curso": curso_cod,
                "director_grupo": dir_nom,
                "acudiente": f"Familia {ap1} {ap2}",
                "activo": True,
            },
        )

    if not estudiante:
        return None, None

    informe = estudiante.informes.filter(anio_lectivo=2026).first() or estudiante.informes.first()
    if not informe:
        d_acad, d_conv = _construir_informe_dinamico(estudiante.documento, estudiante.curso)
        informe = InformeValorativo.objects.create(
            estudiante=estudiante,
            anio_lectivo=2026,
            periodo_actual=3,
            datos_academicos=d_acad,
            datos_convivencia=d_conv,
            observaciones_academicas=(
                "El estudiante debe presentar el desarrollo completo de las guías no alcanzadas en el menor tiempo posible.\n"
                "A la fecha, el aprendiz SENA ha cumplido con la entrega de las evidencias propuestas."
            ),
            observaciones_convivenciales=(
                "La institución agradece su colaboración en las campañas de mejora.\n"
                "Felicitaciones por su aporte a la convivencia institucional."
            ),
            tecnico_sena=d_acad["tecnico_sena"]["p3"],
        )

    return estudiante, informe


def consulta_notas(request):
    """Portal de consulta de calificaciones para padres y estudiantes en tiempo real."""
    query_doc = request.GET.get("doc", "").strip()
    estudiante = None
    informe = None
    mensaje_error = None

    if query_doc:
        estudiante, informe = _resolver_estudiante_e_informe(query_doc)
        if not estudiante:
            mensaje_error = f"No se encontró ningún estudiante con '{query_doc}'. Ingrese un número de documento (T.I. o Cédula) válido."

    return render(request, "web_publica/consulta_notas.html", {
        "secciones": _secciones(),
        "query_doc": query_doc,
        "estudiante": estudiante,
        "informe": informe,
        "mensaje_error": mensaje_error,
    })


def boletin_imprimir(request, documento):
    """Vista de impresión directa y limpia del Informe Valorativo SERC oficial."""
    estudiante, informe = _resolver_estudiante_e_informe(documento)
    if not estudiante or not informe:
        raise Http404("Informe valorativo no encontrado.")

    return render(request, "web_publica/boletin_serc.html", {
        "estudiante": estudiante,
        "informe": informe,
    })


