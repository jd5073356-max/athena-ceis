"""Rutas de la web pública."""
from django.urls import path

from . import views

app_name = "web_publica"

urlpatterns = [
    path("", views.home, name="home"),

    # Guías: Año → Período → Curso → Materia → Guías
    path("guias/", views.guias_anios, name="guias_anios"),
    path("guias/anio/<int:anio_id>/", views.guias_periodos, name="guias_periodos"),
    path("guias/periodo/<int:periodo_id>/", views.guias_cursos, name="guias_cursos"),
    path("guias/curso/<int:curso_id>/", views.guias_materias, name="guias_materias"),
    path("guias/materia/<int:materia_id>/", views.guias_lista, name="guias_lista"),

    # Páginas institucionales y proyectos
    path("colegio/", views.colegio, name="colegio"),
    path("proyectos/", views.proyectos, name="proyectos"),
    path("p/<slug:clave>/", views.pagina_detalle, name="pagina_detalle"),

    # Contenido independiente
    path("noticias/", views.noticias_lista, name="noticias"),
    path("noticias/<int:noticia_id>/", views.noticia_detalle, name="noticia_detalle"),
    path("galeria/", views.galeria, name="galeria"),
    path("videos/", views.videos, name="videos"),
]
