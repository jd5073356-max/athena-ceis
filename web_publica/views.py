"""
Vistas de la web pública.

Solo LEEN de la base (vía los modelos de core). El rector escribe desde el
panel; aquí únicamente se muestra. Las guías se navegan con la jerarquía:
Año → Período → Curso → Materia → Guías.
"""
from django.shortcuts import get_object_or_404, render

from core.models import (
    Anio, Curso, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video,
)


def _secciones() -> dict:
    """Devuelve las secciones de texto indexadas por su clave, para usarlas
    cómodamente en las plantillas (ej. secciones.mision)."""
    return {s.clave: s for s in Seccion.objects.all()}


def home(request):
    """Página de inicio: textos, noticias recientes, videos y galería."""
    contexto = {
        "secciones": _secciones(),
        "noticias": Noticia.objects.filter(activo=True)[:4],
        "videos": Video.objects.all()[:3],
        "imagenes": Imagen.objects.all()[:8],
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
def colegio(request):
    """Listado de páginas institucionales (El Colegio)."""
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "El Colegio",
        "paginas": Seccion.objects.filter(categoria=Seccion.Categoria.COLEGIO),
    })


def proyectos(request):
    """Listado de proyectos transversales."""
    return render(request, "web_publica/paginas_lista.html", {
        "secciones": _secciones(),
        "encabezado": "Nuestros Proyectos",
        "paginas": Seccion.objects.filter(categoria=Seccion.Categoria.PROYECTO),
    })


def pagina_detalle(request, clave):
    """Detalle de una página institucional o de proyecto."""
    pagina = get_object_or_404(
        Seccion, clave=clave,
        categoria__in=[Seccion.Categoria.COLEGIO, Seccion.Categoria.PROYECTO])
    return render(request, "web_publica/pagina_detalle.html", {
        "secciones": _secciones(),
        "pagina": pagina,
    })
