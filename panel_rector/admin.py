"""
Panel del Rector — sobre Django Admin.

El rector entra con usuario y contraseña y gestiona TODO con formularios:
guías (Año→Período→Curso→Materia→Guía), imágenes, noticias, videos y textos.
Nunca toca código.

Para facilitar la carga jerárquica usamos "inlines": al abrir un Año se ven sus
Períodos; dentro de un Período sus Cursos; etc. Además cada lista tiene filtros
para navegar rápido.
"""
from django import forms
from django.contrib import admin

from core.models import (
    Anio, ConfiguracionApariencia, Curso, Documento, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video,
)


class ConfiguracionAparienciaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionApariencia
        fields = "__all__"
        widgets = {
            "color_principal": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "color_secundario": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "color_acento": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "color_acento_suave": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "color_footer": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "color_texto": forms.TextInput(attrs={"type": "color", "style": "height:42px;width:100px;cursor:pointer;"}),
            "tipografia_principal": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "tipografia_titulos": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "tamano_letra": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "radio_bordes": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "intensidad_sombras": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "estilo_menu": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "aviso_tipo": forms.Select(attrs={"style": "max-width:480px;font-size:0.95rem;padding:8px 12px;"}),
            "lema_institucional": forms.TextInput(attrs={"style": "max-width:540px;"}),
            "titulo_hero": forms.TextInput(attrs={"style": "max-width:540px;"}),
            "subtitulo_hero": forms.TextInput(attrs={"style": "max-width:680px;"}),
            "aviso_texto": forms.TextInput(attrs={"style": "max-width:680px;"}),
            "aviso_enlace": forms.TextInput(attrs={"style": "max-width:540px;", "placeholder": "/documentos/ o https://..."}),
            "aviso_texto_enlace": forms.TextInput(attrs={"style": "max-width:280px;"}),
            "telefono_contacto": forms.TextInput(attrs={"style": "max-width:320px;"}),
            "whatsapp_contacto": forms.TextInput(attrs={"style": "max-width:320px;"}),
            "email_contacto": forms.EmailInput(attrs={"style": "max-width:400px;"}),
            "direccion_contacto": forms.TextInput(attrs={"style": "max-width:540px;"}),
            "horario_atencion": forms.TextInput(attrs={"style": "max-width:540px;"}),
            "red_facebook": forms.URLInput(attrs={"style": "max-width:500px;", "placeholder": "https://facebook.com/..."}),
            "red_youtube": forms.URLInput(attrs={"style": "max-width:500px;", "placeholder": "https://youtube.com/..."}),
            "red_instagram": forms.URLInput(attrs={"style": "max-width:500px;", "placeholder": "https://instagram.com/..."}),
            "athena_nombre_visible": forms.TextInput(attrs={"style": "max-width:280px;"}),
            "athena_mensaje_bienvenida": forms.Textarea(attrs={"rows": 3, "style": "max-width:680px;"}),
        }


@admin.register(ConfiguracionApariencia)
class ConfiguracionAparienciaAdmin(admin.ModelAdmin):
    form = ConfiguracionAparienciaForm
    list_display = (
        "__str__",
        "tipografia_principal",
        "tipografia_titulos",
        "tamano_letra",
        "radio_bordes",
        "intensidad_sombras",
        "aviso_activo",
        "athena_activo",
    )
    fieldsets = (
        (
            "Identidad Visual y Marca",
            {
                "description": "Carga el escudo institucional, favicon para la pestaña del navegador y personaliza los textos del lema y portada de bienvenida.",
                "fields": (
                    ("logo_institucional", "favicon_institucional"),
                    "portada_hero",
                    ("lema_institucional", "titulo_hero"),
                    "subtitulo_hero",
                ),
            },
        ),
        (
            "Paleta de Colores Institucional",
            {
                "description": "Selecciona los colores de la cabecera, menú, botones y pie de página con el selector de color.",
                "fields": (
                    ("color_principal", "color_secundario"),
                    ("color_acento", "color_acento_suave"),
                    ("color_footer", "color_texto"),
                ),
            },
        ),
        (
            "Tipografía y Estilo de Fuente",
            {
                "description": "Elige la familia tipográfica para los textos de navegación, párrafos y títulos de la web pública.",
                "fields": ("tipografia_principal", "tipografia_titulos"),
            },
        ),
        (
            "Tamaño de Letra y Accesibilidad",
            {
                "description": "Ajusta la escala proporcional de tamaño de letra de todo el portal público para optimizar la legibilidad.",
                "fields": ("tamano_letra",),
            },
        ),
        (
            "Estilo de Componentes (Diseño y Bordes)",
            {
                "description": "Ajusta el radio de redondeo de las esquinas, la profundidad de sombras y el comportamiento visual del menú principal.",
                "fields": (
                    ("radio_bordes", "intensidad_sombras"),
                    "estilo_menu",
                ),
            },
        ),
        (
            "Barra de Avisos y Anuncios de Urgencia",
            {
                "description": "Activa una franja de notificación en la parte superior del portal para fechas críticas, jornadas o alertas de rectoría.",
                "fields": (
                    ("aviso_activo", "aviso_tipo"),
                    "aviso_texto",
                    ("aviso_enlace", "aviso_texto_enlace"),
                ),
            },
        ),
        (
            "Información de Contacto y Canales Oficiales",
            {
                "description": "Actualiza los teléfonos de atención, correo electrónico, dirección física y redes sociales oficiales del colegio.",
                "fields": (
                    ("telefono_contacto", "whatsapp_contacto"),
                    ("email_contacto", "direccion_contacto"),
                    "horario_atencion",
                    ("red_facebook", "red_youtube", "red_instagram"),
                ),
            },
        ),
        (
            "Asistente Virtual Institucional (Athena)",
            {
                "description": "Configura la visibilidad de la asesora virtual en la web pública, su nombre visible y el mensaje de saludo inicial.",
                "fields": (
                    ("athena_activo", "athena_nombre_visible"),
                    "athena_mensaje_bienvenida",
                ),
            },
        ),
    )

    def has_add_permission(self, request):
        if ConfiguracionApariencia.objects.exists():
            return False
        return super().has_add_permission(request)

    def changelist_view(self, request, extra_context=None):
        config = ConfiguracionApariencia.objects.first()
        if config:
            from django.shortcuts import redirect
            return redirect(f"/admin/core/configuracionapariencia/{config.pk}/change/")
        return super().changelist_view(request, extra_context)


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


class ImagenInline(admin.TabularInline):
    """Permite al rector gestionar las imágenes de una sección desde la sección."""
    model = Imagen
    extra = 1
    fields = ("archivo", "titulo", "orden")
    ordering = ("orden",)


@admin.register(Seccion)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("titulo", "clave", "categoria", "grupo", "orden")
    list_filter = ("categoria", "grupo")
    list_editable = ("orden",)
    search_fields = ("clave", "titulo", "contenido")
    prepopulated_fields = {"clave": ("titulo",)}
    inlines = [ImagenInline]


@admin.register(Imagen)
class ImagenAdmin(admin.ModelAdmin):
    list_display = ("__str__", "seccion", "titulo", "orden", "fecha")
    list_filter = ("seccion",)
    list_editable = ("orden",)
    search_fields = ("titulo",)
    autocomplete_fields = ("seccion",)
    date_hierarchy = "fecha"


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "anio", "nivel", "periodo", "area", "grado", "orden")
    list_filter = ("categoria", "anio", "nivel", "periodo", "area")
    list_editable = ("orden",)
    search_fields = ("titulo", "descripcion", "area", "grado")
    date_hierarchy = "fecha"
    fieldsets = (
        (None, {"fields": ("titulo", "archivo", "categoria")}),
        ("Clasificación (guías SERC)", {
            "fields": ("anio", "nivel", "grado", "periodo", "area"),
            "description": "Igual al Drive: Año → Nivel → Grado → Período → Área. "
                           "En bachillerato el grado suele ir en el título.",
        }),
        ("Extra", {"fields": ("descripcion", "orden"), "classes": ("collapse",)}),
    )
