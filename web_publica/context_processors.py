"""
Menú de la web pública: las mismas divisiones que el sitio Wix oficial.

  INICIO · NOSOTROS (▾) · CIRCULARES, CRONOGRAMA Y GUÍAS · NUESTROS PROYECTOS (▾) · PRE-MATRÍCULA 2026

Los submenús de NOSOTROS y NUESTROS PROYECTOS salen de las secciones del colegio
(categoría 'colegio' y 'proyecto' respectivamente), en su orden.
"""
from core.models import ConfiguracionApariencia, Seccion


def menu_publico(request):
    # No gastar consultas en el panel del rector.
    if request.path.startswith("/admin"):
        return {}
    secciones = list(Seccion.objects.all())
    try:
        config_apariencia = ConfiguracionApariencia.objects.first()
    except Exception:
        config_apariencia = None
    # Ocultar secciones vacias o provisionales sin texto
    secciones_activas = [
        s for s in secciones
        if s.contenido and s.contenido.strip() and s.clave not in {
            "jornada_unica", "autoevaluacion", "familia_calidad", "circulares_padres"
        }
    ]
    return {
        "menu_nosotros": [s for s in secciones_activas if s.categoria == "colegio"],
        "menu_proyectos": [s for s in secciones_activas if s.categoria == "proyecto"],
        "menu_software": [s for s in secciones_activas if s.categoria == "software"],
        "menu_inclusion": [s for s in secciones_activas if s.categoria == "software" and s.clave in {"atdie", "bdei", "eco-inclusivo"}],
        "config_apariencia": config_apariencia,
    }

