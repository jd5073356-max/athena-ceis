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
        for niv in _NIVEL_ORDEN:
            d_niv = [d for d in d_anio if (d.nivel or "") == niv]
            if not d_niv:
                continue
            cursos = []
            distinct_cursos = sorted({_obtener_curso(d) for d in d_niv}, key=curso_key)
            for cur in distinct_cursos:
                d_cur = [d for d in d_niv if _obtener_curso(d) == cur]
                materias = []
                for area in sorted({d.area or "" for d in d_cur}, key=area_key):
                    docs = sorted((d for d in d_cur if (d.area or "") == area),
                                  key=lambda d: (_PERIODO_ORDEN.index(d.periodo) if d.periodo in _PERIODO_ORDEN else 99, d.titulo))
                    materias.append({"materia": area or "General", "docs": docs})
                cursos.append({"curso": cur, "materias": materias})
            niveles.append({"nivel": nivel_label.get(niv, "General"), "cursos": cursos})
        anios.append({"anio": anio or "Sin año", "niveles": niveles})
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
