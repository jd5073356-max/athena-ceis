"""
Menú de la web pública: las mismas divisiones que el sitio Wix oficial.

  INICIO · NOSOTROS (▾) · CIRCULARES, CRONOGRAMA Y GUÍAS · NUESTROS PROYECTOS (▾) · PRE-MATRÍCULA 2026

Los submenús de NOSOTROS y NUESTROS PROYECTOS salen de las secciones del colegio
(categoría 'colegio' y 'proyecto' respectivamente), en su orden.
"""
from core.models import Seccion


def menu_publico(request):
    # No gastar consultas en el panel del rector.
    if request.path.startswith("/admin"):
        return {}
    secciones = list(Seccion.objects.all())
    return {
        "menu_nosotros": [s for s in secciones if s.categoria == "colegio"],
        "menu_proyectos": [s for s in secciones if s.categoria == "proyecto"],
    }
