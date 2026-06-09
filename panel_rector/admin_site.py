from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.urls import reverse
from django.utils import timezone


class AthenaAdminSite(admin.AdminSite):
    site_header = "Athena · Panel del Rector"
    site_title = "Athena"
    index_title = "Gestión del sitio del colegio"

    # =======================================================================
    #  Inicio del panel: dashboard "Vista General" (diseño Stitch).
    #  Todos los números son REALES (de la base), no maquetas.
    # =======================================================================
    def index(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), **self._dashboard_context()}
        return super().index(request, extra_context)

    def _dashboard_context(self):
        from core.models import Curso, Guia, Imagen, Materia, Noticia, Video

        hoy = timezone.localdate()
        inicio_mes = hoy.replace(day=1)

        # --- Tarjetas KPI (conteos reales) ---
        kpis = [
            {
                "label": "Cursos", "icon": "school", "tone": "primary",
                "value": Curso.objects.count(),
                "sub_icon": "menu_book",
                "sub": f"{Materia.objects.count()} materias",
            },
            {
                "label": "Guías de estudio", "icon": "description", "tone": "tertiary",
                "value": Guia.objects.count(),
                "sub_icon": "trending_up",
                "sub": f"+{Guia.objects.filter(fecha_publicacion__gte=inicio_mes).count()} este mes",
            },
            {
                "label": "Noticias", "icon": "newspaper", "tone": "primary",
                "value": Noticia.objects.count(),
                "sub_icon": "visibility",
                "sub": f"{Noticia.objects.filter(activo=True).count()} activas",
            },
            {
                "label": "Galería", "icon": "image", "tone": "secondary",
                "value": Imagen.objects.count(),
                "sub_icon": "photo_library",
                "sub": "imágenes públicas",
            },
        ]

        # --- Gráfico: contenido publicado por mes (últimos 6 meses) ---
        conteos = {}
        for modelo, campo in ((Guia, "fecha_publicacion"), (Noticia, "fecha_publicacion"),
                              (Imagen, "fecha"), (Video, "fecha")):
            filas = modelo.objects.annotate(m=TruncMonth(campo)).values("m").annotate(c=Count("id"))
            for fila in filas:
                if fila["m"]:
                    clave = (fila["m"].year, fila["m"].month)
                    conteos[clave] = conteos.get(clave, 0) + fila["c"]

        meses_es = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
        ventana = []
        for i in range(5, -1, -1):
            yy, mm = hoy.year, hoy.month - i
            while mm <= 0:
                mm += 12
                yy -= 1
            ventana.append((yy, mm))
        valores = [conteos.get(k, 0) for k in ventana]
        tope = max(valores) or 1
        grafico = [
            {"label": meses_es[mm - 1], "value": v,
             "pct": max(round(v / tope * 100), 6), "activo": idx == len(ventana) - 1}
            for idx, ((yy, mm), v) in enumerate(zip(ventana, valores))
        ]

        # --- Acciones rápidas (enlaces reales a los formularios) ---
        acciones = [
            {"label": "Nuevo usuario", "icon": "person_add", "tone": "primary",
             "url": reverse("admin:auth_user_add")},
            {"label": "Publicar noticia", "icon": "post_add", "tone": "tertiary",
             "url": reverse("admin:core_noticia_add")},
            {"label": "Subir imagen", "icon": "add_photo_alternate", "tone": "secondary",
             "url": reverse("admin:core_imagen_add")},
            {"label": "Gestión de períodos", "icon": "event", "tone": "muted",
             "url": reverse("admin:core_periodo_changelist")},
        ]

        # --- Actividad reciente (log de auditoría real de Django) ---
        recientes = []
        for e in LogEntry.objects.select_related("content_type", "user").order_by("-action_time")[:6]:
            if e.action_flag == ADDITION:
                verbo, icon, estado, tono = "Creó", "add_circle", "Creado", "ok"
            elif e.action_flag == CHANGE:
                verbo, icon, estado, tono = "Actualizó", "edit", "Actualizado", "ok"
            else:
                verbo, icon, estado, tono = "Eliminó", "delete", "Eliminado", "err"
            modelo = e.content_type.name if e.content_type else "registro"
            recientes.append({
                "icon": icon, "tono": tono, "estado": estado,
                "accion": f"{verbo} {modelo}",
                "objeto": e.object_repr,
                "usuario": e.user.get_full_name() or e.user.get_username(),
                "cuando": e.action_time,
            })

        return {
            "dash_kpis": kpis,
            "dash_grafico": grafico,
            "dash_acciones": acciones,
            "dash_recientes": recientes,
        }

    def get_app_list(self, request, app_label=None):
        """Agrupa los modelos en secciones personalizadas en el sidebar y el index."""
        app_list = super().get_app_list(request, app_label)
        
        # Mapeamos los modelos por su clave completa (ej: 'auth.User')
        all_models = {}
        for app in app_list:
            for model in app.get('models', []):
                key = f"{app['app_label']}.{model['object_name']}"
                all_models[key] = model

        # Configuración de las secciones requeridas
        sections_config = [
            {
                'name': 'ADMINISTRACIÓN CENTRAL',
                'app_label': 'admin_central',
                'app_url': '#',
                'has_module_perms': True,
                'models_keys': [
                    'auth.Group',
                    'auth.User',
                ]
            },
            {
                'name': 'NÚCLEO (DATOS DEL COLEGIO)',
                'app_label': 'nucleo_colegio',
                'app_url': '#',
                'has_module_perms': True,
                'models_keys': [
                    'core.Anio',
                    'core.Periodo',
                    'core.Curso',
                    'core.Materia',
                    'core.Guia',
                    'core.Imagen',
                    'core.Noticia',
                    'core.Seccion',
                    'core.Video',
                ]
            }
        ]

        # Construimos la nueva lista de aplicaciones agrupadas
        new_app_list = []
        for sec in sections_config:
            section_models = []
            for m_key in sec['models_keys']:
                if m_key in all_models:
                    section_models.append(all_models[m_key])
            
            if section_models:
                new_app_list.append({
                    'name': sec['name'],
                    'app_label': sec['app_label'],
                    'app_url': sec['app_url'],
                    'has_module_perms': sec['has_module_perms'],
                    'models': section_models,
                })
        
        # Agregamos cualquier modelo restante que no esté mapeado explícitamente (por robustez)
        placed_keys = set()
        for sec in sections_config:
            placed_keys.update(sec['models_keys'])
            
        remaining_models = []
        for key, model in all_models.items():
            if key not in placed_keys:
                remaining_models.append(model)
                
        if remaining_models:
            new_app_list.append({
                'name': 'OTROS MODELOS',
                'app_label': 'otros_modelos',
                'app_url': '#',
                'has_module_perms': True,
                'models': remaining_models,
            })
            
        return new_app_list
