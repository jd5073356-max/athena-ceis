"""Helpers de plantilla para los listados del Panel del Rector (estilo Stitch).

Todo sale de datos REALES del modelo; no se inventa nada.
"""
from django import template
from django.contrib.auth.models import Group

register = template.Library()


def _rol(user):
    if user.is_superuser:
        return "Administrador"
    g = user.groups.first()
    if g:
        return g.name
    if user.is_staff:
        return "Equipo"
    return "Sin rol"


@register.simple_tag
def ath_groups():
    return Group.objects.all()


@register.filter
def ath_initials(user):
    fn = (getattr(user, "first_name", "") or "").strip()
    ln = (getattr(user, "last_name", "") or "").strip()
    if fn or ln:
        return ((fn[:1] + ln[:1]).upper()) or fn[:2].upper()
    return user.get_username()[:2].upper()


@register.filter
def ath_fullname(user):
    return user.get_full_name() or user.get_username()


@register.filter
def ath_rol(user):
    return _rol(user)


@register.filter
def ath_rol_class(user):
    r = _rol(user).lower()
    if "admin" in r:
        return "gold"
    if "docente" in r or "profesor" in r:
        return "blue"
    if "estudiante" in r or "alumno" in r:
        return "grey"
    return "slate"


@register.simple_tag
def ath_showing(cl, noun="registros"):
    try:
        per = cl.paginator.per_page
        total = cl.result_count
        if not total:
            return f"0 {noun}"
        start = (cl.page_num - 1) * per + 1
        end = min(cl.page_num * per, total)
        return f"Mostrando {start}–{end} de {total} {noun}"
    except Exception:
        return ""


@register.simple_tag
def ath_page_url(cl, n):
    return cl.get_query_string({"p": n})


@register.simple_tag
def ath_noticia_stats():
    from core.models import Noticia
    total = Noticia.objects.count()
    pub = Noticia.objects.filter(activo=True).count()
    return {
        "total": total,
        "pub": pub,
        "bor": total - pub,
        "pub_pct": round(pub / total * 100) if total else 0,
    }


@register.simple_tag
def ath_curso_stats():
    from core.models import Curso, Materia
    return {
        "cursos": Curso.objects.count(),
        "materias": Materia.objects.count(),
        "sin_materias": Curso.objects.filter(materias__isnull=True).count(),
    }


@register.simple_tag
def ath_periodos():
    from core.models import Periodo
    return Periodo.objects.select_related("anio").all()


@register.simple_tag
def ath_materias_grouped(cl):
    from collections import OrderedDict
    groups = OrderedDict()
    for m in cl.result_list:
        groups.setdefault(m.curso, []).append(m)
    return sorted(groups.items(), key=lambda kv: str(kv[0]))


@register.simple_tag
def ath_anio_stats():
    from core.models import Anio
    activo = Anio.objects.filter(activo=True).order_by("-anio").first()
    return {
        "activo": activo,
        "activo_periodos": activo.periodos.count() if activo else 0,
        "total": Anio.objects.count(),
    }


@register.simple_tag
def ath_periodo_stats():
    from core.models import Curso, Periodo
    return {
        "periodos": Periodo.objects.count(),
        "cursos": Curso.objects.count(),
    }


@register.simple_tag
def ath_materias_all():
    from core.models import Materia
    return Materia.objects.select_related("curso").all()


@register.filter
def ath_yt_thumb(video):
    import re
    m = re.search(
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
        getattr(video, "youtube_url", "") or "",
    )
    return f"https://img.youtube.com/vi/{m.group(1)}/hqdefault.jpg" if m else ""
