"""
Panel Administrativo — sobre Django Admin.

El rector entra con usuario y contraseña y gestiona TODO con formularios:
guías (Año→Período→Curso→Materia→Guía), imágenes, noticias, videos y textos.
Nunca toca código.

Para facilitar la carga jerárquica usamos "inlines": al abrir un Año se ven sus
Períodos; dentro de un Período sus Cursos; etc. Además cada lista tiene filtros
para navegar rápido.
"""
from django import forms
from django.contrib import admin
from django.urls import path

from core.models import (
    Anio, ComunicadoOficial, ConfiguracionApariencia, Curso, DatasetAnalisis, Documento, Estudiante, Guia, Imagen,
    InformeValorativo, Materia, Noticia, Periodo, Seccion, Video,
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
    change_list_template = "admin/core/documento/change_list.html"
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

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "carga-masiva/",
                self.admin_site.admin_view(self.carga_masiva_view),
                name="core_documento_carga_masiva",
            ),
        ]
        return custom_urls + urls

    def carga_masiva_view(self, request):
        from django.http import JsonResponse
        from django.shortcuts import render
        from django.db import connections
        from core.parser_guias import parsear_nombre_guia

        if request.method == "POST":
            archivos = request.FILES.getlist("archivos")
            default_anio = int(request.POST.get("default_anio", 2026))
            default_periodo = request.POST.get("default_periodo", "").strip()
            categoria = request.POST.get("default_categoria", "guia").strip()

            if not archivos:
                return JsonResponse({"status": "error", "error": "No se enviaron archivos."}, status=400)

            # Sincronizar secuencia en PostgreSQL para evitar errores de clave primaria
            try:
                with connections["default"].cursor() as cursor:
                    cursor.execute("""
                        SELECT setval(pg_get_serial_sequence('"DOCUMENTOS"', 'id'), coalesce(max(id), 1) + 1, false) FROM "DOCUMENTOS";
                    """)
            except Exception:
                pass

            creados = 0
            actualizados = 0
            procesados = []

            for f in archivos:
                meta = parsear_nombre_guia(
                    f.name,
                    default_anio=default_anio,
                    default_periodo=default_periodo,
                )
                doc, created = Documento.objects.update_or_create(
                    categoria=categoria,
                    anio=meta["anio"],
                    titulo=meta["titulo"],
                    defaults={
                        "nivel": meta["nivel"],
                        "grado": meta["grado"],
                        "periodo": meta["periodo"],
                        "area": meta["area"],
                    },
                )
                doc.archivo.save(meta["s3_key"], f, save=True)

                if created:
                    creados += 1
                else:
                    actualizados += 1

                procesados.append({
                    "titulo": meta["titulo"],
                    "archivo": meta["s3_key"],
                    "nivel": meta["nivel"],
                    "grado": meta["grado"],
                    "periodo": meta["periodo"],
                    "area": meta["area"],
                    "estado": "creado" if created else "actualizado",
                })

            # Replicar en SQLite local si existe
            try:
                import sqlite3
                from pathlib import Path
                from datetime import date
                from django.conf import settings

                sqlite_path = Path(settings.BASE_DIR) / "db.sqlite3"
                if sqlite_path.exists():
                    conn = sqlite3.connect(sqlite_path)
                    c = conn.cursor()
                    hoy = date.today().isoformat()
                    for p in procesados:
                        c.execute(
                            "SELECT id FROM DOCUMENTOS WHERE categoria=? AND anio=? AND titulo=?",
                            (categoria, default_anio, p["titulo"]),
                        )
                        r = c.fetchone()
                        if r:
                            c.execute(
                                """
                                UPDATE DOCUMENTOS
                                SET nivel=?, grado=?, periodo=?, area=?, RUTA_ARCHIVO=?
                                WHERE id=?
                                """,
                                (p["nivel"], p["grado"], p["periodo"], p["area"], p["archivo"], r[0]),
                            )
                        else:
                            c.execute(
                                """
                                INSERT INTO DOCUMENTOS
                                (titulo, RUTA_ARCHIVO, categoria, anio, nivel, grado, periodo, area, descripcion, orden, fecha)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, '', 0, ?)
                                """,
                                (p["titulo"], p["archivo"], categoria, default_anio, p["nivel"], p["grado"], p["periodo"], p["area"], hoy),
                            )
                    conn.commit()
                    conn.close()
            except Exception:
                pass

            return JsonResponse({
                "status": "ok",
                "total": len(archivos),
                "creados": creados,
                "actualizados": actualizados,
                "items": procesados,
            })

        context = {
            **self.admin_site.each_context(request),
            "opts": self.model._meta,
            "has_view_permission": self.has_view_permission(request),
        }
        return render(request, "admin/core/documento/carga_masiva.html", context)


# ===========================================================================
#  Seguimiento Académico y Boletines SERC
# ===========================================================================
@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ("documento", "apellidos", "nombres", "curso", "grado", "director_grupo", "activo")
    list_filter = ("curso", "grado", "activo")
    search_fields = ("documento", "apellidos", "nombres", "acudiente")
    ordering = ("curso", "apellidos", "nombres")

    def get_urls(self):
        urls = super().get_urls()
        from django.shortcuts import redirect
        custom_urls = [
            path(
                "importar-excel/",
                self.admin_site.admin_view(lambda req: redirect("admin:core_informevalorativo_importar_excel")),
                name="core_estudiante_importar_excel",
            ),
        ]
        return custom_urls + urls


@admin.register(InformeValorativo)
class InformeValorativoAdmin(admin.ModelAdmin):
    list_display = ("estudiante", "anio_lectivo", "periodo_actual", "tecnico_sena", "fecha_emision")
    list_filter = ("anio_lectivo", "periodo_actual", "estudiante__curso")
    search_fields = ("estudiante__documento", "estudiante__apellidos", "estudiante__nombres", "estudiante__curso")
    autocomplete_fields = ("estudiante",)

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "importar-excel/",
                self.admin_site.admin_view(self.importar_excel_view),
                name="core_informevalorativo_importar_excel",
            ),
        ]
        return custom_urls + urls

    def importar_excel_view(self, request):
        import os
        import tempfile
        from django.shortcuts import render
        from django.contrib import messages
        from django.http import JsonResponse
        from django.utils import timezone
        from core.models import ConfiguracionSincronizacion
        from core.sync_service import ejecutar_sincronizacion_excel, leer_estado_sync, sincronizar_desde_nube

        resultado = None
        error_msg = None

        sync_config, _ = ConfiguracionSincronizacion.objects.get_or_create(id=1)

        if request.method == "POST":
            accion = request.POST.get("accion", "excel").strip()

            if accion == "guardar_firmas":
                sync_config.rector_nombre = request.POST.get("rector_nombre", "").strip() or "Lic. Juan Carlos Aguirre Nieto"
                sync_config.rector_cargo = request.POST.get("rector_cargo", "").strip() or "Rector"
                sync_config.secretario_nombre = request.POST.get("secretario_nombre", "").strip() or "Elder Uriel Páez Córdoba"
                sync_config.secretario_cargo = request.POST.get("secretario_cargo", "").strip() or "Secretario Académico"
                if request.POST.get("restaurar_firma_rector") == "1":
                    sync_config.firma_rector = None
                elif request.FILES.get("firma_rector"):
                    sync_config.firma_rector = request.FILES["firma_rector"]
                if request.POST.get("restaurar_firma_secretario") == "1":
                    sync_config.firma_secretario = None
                elif request.FILES.get("firma_secretario"):
                    sync_config.firma_secretario = request.FILES["firma_secretario"]
                sync_config.save()
                messages.success(request, "Firmas y cargos oficiales del Boletín SERC actualizados correctamente.")
            elif accion in ("guardar_api", "sincronizar_nube"):
                sync_config.proveedor = request.POST.get("proveedor", sync_config.proveedor).strip()
                sync_config.url_hoja = request.POST.get("url_hoja", "").strip()
                nueva_key = request.POST.get("api_key", "").strip()
                if nueva_key and not nueva_key.startswith("••••"):
                    sync_config.api_key = nueva_key
                elif request.POST.get("limpiar_api_key") == "1":
                    sync_config.api_key = ""
                try:
                    sync_config.frecuencia_minutos = max(1, int(request.POST.get("frecuencia_minutos", 15)))
                except Exception:
                    sync_config.frecuencia_minutos = 15
                sync_config.activo = request.POST.get("activo") == "1"
                sync_config.save()

                if accion == "guardar_api":
                    messages.success(request, "Configuración de API Key y sincronización en la nube guardada correctamente.")
                else:
                    res = sincronizar_desde_nube(config=sync_config, forzar=True)
                    if res.get("exito"):
                        resultado = res
                        messages.success(request, f"¡Sincronización desde la nube exitosa! {res.get('mensaje', '')}")
                    else:
                        error_msg = res.get("error", "No se pudo sincronizar desde la nube.")
                        messages.error(request, error_msg)
            else:
                anio_lectivo = int(request.POST.get("anio_lectivo", 2026))
                periodo_raw = str(request.POST.get("periodo_actual", "auto")).strip().lower()
                periodo_actual = None if periodo_raw in ("", "auto", "0") else int(periodo_raw)
                usar_institucional = request.POST.get("usar_institucional") == "1"
                archivo = request.FILES.get("archivo_excel")

                if not archivo and not usar_institucional:
                    error_msg = "Debe seleccionar un archivo Excel (.xlsx) o elegir la sincronización institucional."
                else:
                    ruta_tmp = None
                    try:
                        if archivo:
                            nombre_seguro = f"sabana_upload_{request.user.id}_{int(timezone.now().timestamp())}.xlsx"
                            ruta_tmp = os.path.join(tempfile.gettempdir(), nombre_seguro)
                            with open(ruta_tmp, "wb") as f_out:
                                for chunk in archivo.chunks():
                                    f_out.write(chunk)
                            res = ejecutar_sincronizacion_excel(
                                ruta_archivo=ruta_tmp,
                                forzar=True,
                                anio_lectivo=anio_lectivo,
                                periodo_actual=periodo_actual,
                            )
                        else:
                            res = ejecutar_sincronizacion_excel(
                                forzar=True,
                                anio_lectivo=anio_lectivo,
                                periodo_actual=periodo_actual,
                            )

                        if res.get("exito"):
                            resultado = res
                            pers = ", ".join(map(str, res.get("periodos_detectados", [res.get("periodo_actual", 3)])))
                            messages.success(
                                request,
                                f"¡Sincronización completada! Se cargaron/actualizaron {res['estudiantes_procesados']} estudiantes y sus informes valorativos SERC (Periodo {pers} · {len(res.get('cursos_procesados', []))} cursos)."
                            )
                        else:
                            error_msg = res.get("error", "Error procesando el archivo.")
                            messages.error(request, error_msg)
                    except Exception as e:
                        error_msg = f"Ocurrió un error al procesar el archivo: {str(e)}"
                        messages.error(request, error_msg)
                    finally:
                        if ruta_tmp and os.path.exists(ruta_tmp):
                            try:
                                os.remove(ruta_tmp)
                            except Exception:
                                pass

            if request.headers.get("x-requested-with") == "XMLHttpRequest":
                if error_msg:
                    return JsonResponse({"status": "error", "message": error_msg}, status=400)
                return JsonResponse({"status": "ok", "resultado": resultado})

        raw_key = (sync_config.api_key or "").strip()
        api_key_masked = f"••••••••••••{raw_key[-4:]}" if len(raw_key) > 4 else ("••••••" if raw_key else "")
        webhook_url = request.build_absolute_uri("/api/sincronizar-sabana/")

        sync_info = leer_estado_sync()
        context = {
            **self.admin_site.each_context(request),
            "title": "Carga Masiva de Sábana Excel (SERC)",
            "subtitle": "Importación general de estudiantes y calificaciones",
            "total_estudiantes": Estudiante.objects.count(),
            "total_informes": InformeValorativo.objects.count(),
            "sync_info": sync_info,
            "sync_config": sync_config,
            "api_key_masked": api_key_masked,
            "has_api_key": bool(raw_key),
            "webhook_url": webhook_url,
            "resultado": resultado,
            "error_msg": error_msg,
            "opts": self.model._meta,
        }
        return render(request, "admin/core/informevalorativo/importar_excel.html", context)


@admin.register(DatasetAnalisis)
class DatasetAnalisisAdmin(admin.ModelAdmin):
    list_display = ("titulo", "categoria", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("categoria", "fecha_creacion")
    search_fields = ("titulo", "descripcion")


@admin.register(ComunicadoOficial)
class ComunicadoOficialAdmin(admin.ModelAdmin):
    list_display = ("numero_radicado", "titulo", "tipo", "fecha_emision", "publicado_web")
    list_filter = ("tipo", "fecha_emision", "publicado_web")
    search_fields = ("numero_radicado", "titulo", "asunto", "destinatario")
    ordering = ("-fecha_emision", "-id")



