from django.contrib.auth.models import Group, User
from django.db.models import Count, Prefetch

from core.models import Anio, Curso, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video


def admin_dashboard_context(request):
    if not request.user.is_authenticated:
        return {}

    return {
        "admin_groups": Group.objects.annotate(
            user_count=Count("user"),
        ).order_by("name"),
        "admin_users": User.objects.prefetch_related(
            Prefetch("groups", to_attr="grupos_list"),
        ).order_by("username"),
        "admin_anios": Anio.objects.annotate(
            periodo_count=Count("periodos"),
        ).order_by("-anio"),
        "admin_cursos": Curso.objects.select_related(
            "periodo__anio",
        ).annotate(
            materia_count=Count("materias"),
        ).order_by("nombre"),
        "admin_guias": Guia.objects.select_related(
            "materia__curso__periodo__anio",
        ).order_by("-fecha_publicacion"),
        "admin_materias": Materia.objects.select_related(
            "curso__periodo__anio",
        ).annotate(
            guia_count=Count("guias"),
        ).order_by("nombre"),
        "admin_noticias": Noticia.objects.all().order_by("-fecha_publicacion"),
        "admin_periodos": Periodo.objects.select_related(
            "anio",
        ).annotate(
            curso_count=Count("cursos"),
        ).order_by("anio__anio", "numero"),
        "admin_secciones": Seccion.objects.all().order_by("categoria", "orden", "clave"),
        "admin_videos": Video.objects.all().order_by("-fecha"),
        "admin_imagenes": Imagen.objects.all().order_by("-fecha"),
    }
