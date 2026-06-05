"""
Panel del Rector — sobre Django Admin.

El rector entra con usuario y contraseña y gestiona TODO con formularios:
guías (Año→Período→Curso→Materia→Guía), imágenes, noticias, videos y textos.
Nunca toca código.

Para facilitar la carga jerárquica usamos "inlines": al abrir un Año se ven sus
Períodos; dentro de un Período sus Cursos; etc. Además cada lista tiene filtros
para navegar rápido.
"""
from django.contrib import admin

from core.models import (
    Anio, Curso, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video,
)

# --- Marca del panel (en español) ------------------------------------------
# El sitio de administración personalizado (AthenaAdminSite) está definido en admin_site.py


# ===========================================================================
#  Inlines: edición jerárquica guiada
# ===========================================================================
class PeriodoInline(admin.TabularInline):
    model = Periodo
    extra = 0


class CursoInline(admin.TabularInline):
    model = Curso
    extra = 0


class MateriaInline(admin.TabularInline):
    model = Materia
    extra = 0


class GuiaInline(admin.TabularInline):
    model = Guia
    extra = 0
    fields = ("titulo", "archivo", "descripcion")


# ===========================================================================
#  Jerarquía de guías
# ===========================================================================
@admin.register(Anio)
class AnioAdmin(admin.ModelAdmin):
    list_display = ("anio", "activo")
    list_editable = ("activo",)
    search_fields = ("anio",)
    inlines = [PeriodoInline]


@admin.register(Periodo)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "anio", "numero", "nombre")
    list_filter = ("anio",)
    search_fields = ("nombre", "anio__anio")
    autocomplete_fields = ("anio",)
    inlines = [CursoInline]


@admin.register(Curso)
class CursoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "periodo", "nivel")
    list_filter = ("periodo__anio", "periodo")
    search_fields = ("nombre", "nivel")
    autocomplete_fields = ("periodo",)
    inlines = [MateriaInline]


@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "curso")
    list_filter = ("curso__periodo__anio", "curso__periodo", "curso")
    search_fields = ("nombre", "curso__nombre")
    autocomplete_fields = ("curso",)
    inlines = [GuiaInline]


@admin.register(Guia)
class GuiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "materia", "fecha_publicacion")
    list_filter = (
        "materia__curso__periodo__anio",
        "materia__curso__periodo",
        "materia__curso",
        "materia",
    )
    search_fields = ("titulo", "descripcion", "materia__nombre")
    autocomplete_fields = ("materia",)
    date_hierarchy = "fecha_publicacion"


# ===========================================================================
#  Contenido independiente
# ===========================================================================
@admin.register(Noticia)
class NoticiaAdmin(admin.ModelAdmin):
    list_display = ("titulo", "fecha_publicacion", "activo")
    list_editable = ("activo",)
    list_filter = ("activo", "fecha_publicacion")
    search_fields = ("titulo", "cuerpo")
    date_hierarchy = "fecha_publicacion"


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "youtube_url", "fecha")
    search_fields = ("titulo", "descripcion")


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "clave", "categoria", "orden")
    list_filter = ("categoria",)
    list_editable = ("orden",)
    search_fields = ("clave", "titulo", "contenido")
    prepopulated_fields = {"clave": ("titulo",)}


@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ("__str__", "titulo", "fecha")
    search_fields = ("titulo",)
    date_hierarchy = "fecha"
