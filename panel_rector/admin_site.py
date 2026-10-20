from django.contrib import admin
from django.contrib.admin.models import ADDITION, CHANGE, LogEntry
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.urls import reverse
from django.utils import timezone


class AthenaAdminSite(admin.AdminSite):
    site_header = "Athena · Panel Administrativo"
    site_title = "Athena"
    index_title = "Gestión del sitio del colegio"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path("analitica/", self.admin_view(self.analitica_view), name="analitica"),
            path("analitica/datasets/", self.admin_view(self.analitica_datasets_view), name="analitica_datasets"),
            path("analitica/datasets/<int:dataset_id>/", self.admin_view(self.analitica_dataset_detalle_view), name="analitica_dataset_detalle"),
            path("api/analitica/explicar/", self.admin_view(self.analitica_explicar_api), name="analitica_explicar_api"),
            path("api/analitica/datos/", self.admin_view(self.analitica_datos_api), name="analitica_datos_api"),
            path("api/analitica/datasets/upload/", self.admin_view(self.analitica_dataset_upload_api), name="analitica_dataset_upload_api"),
            path("api/analitica/datasets/<int:dataset_id>/explicar/", self.admin_view(self.analitica_dataset_explicar_api), name="analitica_dataset_explicar_api"),
            path("despacho/", self.admin_view(self.despacho_circulares_view), name="despacho_circulares"),
            path("despacho/crear/", self.admin_view(self.despacho_crear_view), name="despacho_crear"),
            path("despacho/<int:comunicado_id>/", self.admin_view(self.despacho_detalle_view), name="despacho_detalle"),
            path("api/despacho/redactar/", self.admin_view(self.despacho_redactar_api), name="despacho_redactar_api"),
            path("api/despacho/guardar/", self.admin_view(self.despacho_guardar_api), name="despacho_guardar_api"),
        ]
        return custom_urls + urls

    def analitica_datasets_view(self, request):
        from django.template.response import TemplateResponse
        from core.models import DatasetAnalisis

        datasets = DatasetAnalisis.objects.all().order_by("-fecha_creacion")
        context = {
            **self.each_context(request),
            "title": "Analizador de Datasets y Pruebas Externas",
            "subtitle": "Ingesta de Excels/CSVs (ICFES, Evaluar para Avanzar, caracterización) y diagnóstico con Athena IA (Qwen 3.8)",
            "datasets": datasets,
        }
        return TemplateResponse(request, "admin/analitica_datasets.html", context)

    def analitica_dataset_detalle_view(self, request, dataset_id):
        import json
        from django.shortcuts import get_object_or_404
        from django.template.response import TemplateResponse
        from core.models import DatasetAnalisis

        dataset = get_object_or_404(DatasetAnalisis, id=dataset_id)
        datos = dataset.datos_normalizados or {}
        context = {
            **self.each_context(request),
            "title": dataset.titulo,
            "subtitle": f"{dataset.get_categoria_display()} · Diagnóstico cuantitativo Athena IA (Qwen 3.8)",
            "dataset": dataset,
            "datos": datos,
            "datos_json": json.dumps(datos),
        }
        return TemplateResponse(request, "admin/analitica_dataset_detalle.html", context)

    def analitica_dataset_upload_api(self, request):
        import os
        from django.shortcuts import redirect
        from django.contrib import messages
        from core.models import DatasetAnalisis
        from core.dataset_parser import procesar_archivo_dataset, generar_diagnostico_dataset_ia

        if request.method != "POST":
            return redirect("admin:analitica_datasets")

        archivo = request.FILES.get("archivo")
        if not archivo:
            messages.error(request, "Debe seleccionar un archivo Excel (.xlsx, .xls) o CSV válido.")
            return redirect("admin:analitica_datasets")

        titulo = request.POST.get("titulo", "").strip() or os.path.splitext(archivo.name)[0].strip()
        categoria = request.POST.get("categoria", "icfes").strip()
        descripcion = request.POST.get("descripcion", "").strip()

        try:
            datos_norm = procesar_archivo_dataset(archivo, archivo.name)
            archivo.seek(0)
            ds = DatasetAnalisis.objects.create(
                titulo=titulo,
                categoria=categoria,
                descripcion=descripcion,
                datos_normalizados=datos_norm,
            )
            ds.archivo.save(archivo.name, archivo, save=True)

            # Generar diagnóstico con Qwen 3.8 27B
            diag = generar_diagnostico_dataset_ia(ds)
            ds.diagnostico_ia = diag
            ds.save()

            messages.success(request, f"Dataset '{ds.titulo}' procesado y analizado con éxito por Athena IA.")
            return redirect("admin:analitica_dataset_detalle", dataset_id=ds.id)
        except Exception as e:
            messages.error(request, f"Error al procesar el archivo: {str(e)}")
            return redirect("admin:analitica_datasets")

    def analitica_dataset_explicar_api(self, request, dataset_id):
        from django.http import JsonResponse
        from django.shortcuts import get_object_or_404
        from core.models import DatasetAnalisis
        from core.dataset_parser import generar_diagnostico_dataset_ia

        dataset = get_object_or_404(DatasetAnalisis, id=dataset_id)
        diag = generar_diagnostico_dataset_ia(dataset)
        dataset.diagnostico_ia = diag
        dataset.save(update_fields=["diagnostico_ia"])
        return JsonResponse({"diagnostico": diag})

    def despacho_circulares_view(self, request):
        from django.template.response import TemplateResponse
        from core.models import ComunicadoOficial

        circulares = ComunicadoOficial.objects.all().order_by("-fecha_emision", "-id")
        context = {
            **self.each_context(request),
            "title": "Despacho Rectoral · Circulares y Resoluciones",
            "subtitle": "Generación instantánea de actos administrativos y circulares con membrete oficial y difusión por WhatsApp",
            "comunicados": circulares,
        }
        return TemplateResponse(request, "admin/despacho_circulares.html", context)

    def despacho_crear_view(self, request):
        from django.template.response import TemplateResponse
        from core.despacho_service import generar_siguiente_radicado

        tipo_default = request.GET.get("tipo", "circular")
        context = {
            **self.each_context(request),
            "title": "Redactor Oficial del Despacho Rectoral",
            "subtitle": "Generación asistida por Athena IA (Qwen 3.8) con membrete oficial y texto para WhatsApp",
            "siguiente_radicado": generar_siguiente_radicado(tipo_default),
            "tipo_default": tipo_default,
        }
        return TemplateResponse(request, "admin/despacho_crear.html", context)

    def despacho_detalle_view(self, request, comunicado_id):
        from django.shortcuts import get_object_or_404
        from django.template.response import TemplateResponse
        from core.models import ComunicadoOficial

        comunicado = get_object_or_404(ComunicadoOficial, id=comunicado_id)
        host = request.get_host()
        protocol = "https" if request.is_secure() else "http"
        url_publica = f"{protocol}://{host}/circular/{comunicado.id}/"

        wapp_msg = f"{comunicado.resumen_whatsapp}\n\nConsulte el documento oficial con membrete en: {url_publica}"

        context = {
            **self.each_context(request),
            "title": comunicado.numero_radicado,
            "subtitle": f"{comunicado.get_tipo_display()} · {comunicado.fecha_emision}",
            "comunicado": comunicado,
            "url_publica": url_publica,
            "wapp_msg": wapp_msg,
        }
        return TemplateResponse(request, "admin/despacho_detalle.html", context)

    def despacho_redactar_api(self, request):
        import json
        from django.http import JsonResponse
        from core.despacho_service import redactar_comunicado_ia

        if request.method != "POST":
            return JsonResponse({"error": "Método no permitido"}, status=405)

        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = request.POST.dict()

        tipo = data.get("tipo", "circular")
        asunto = data.get("asunto", "").strip()
        destinatario = data.get("destinatario", "").strip() or "Padres de Familia y Comunidad Educativa"
        instrucciones = data.get("instrucciones", "").strip()
        radicado = data.get("radicado", "").strip()
        fecha = data.get("fecha", "").strip()

        if not asunto:
            return JsonResponse({"error": "El asunto del documento es obligatorio"}, status=400)

        resultado = redactar_comunicado_ia(
            tipo=tipo,
            asunto=asunto,
            destinatario=destinatario,
            instrucciones=instrucciones,
            radicado=radicado,
            fecha=fecha,
        )
        return JsonResponse(resultado)

    def despacho_guardar_api(self, request):
        from django.shortcuts import redirect
        from django.contrib import messages
        from core.models import ComunicadoOficial, Documento

        if request.method != "POST":
            return redirect("admin:despacho_circulares")

        tipo = request.POST.get("tipo", "circular")
        radicado = request.POST.get("numero_radicado", "").strip()
        titulo = request.POST.get("titulo", "").strip()
        asunto = request.POST.get("asunto", "").strip()
        destinatario = request.POST.get("destinatario", "").strip()
        cuerpo_html = request.POST.get("cuerpo_html", "").strip()
        resumen_whatsapp = request.POST.get("resumen_whatsapp", "").strip()
        firmado_por = request.POST.get("firmado_por", "Lic. Juan Carlos Aguirre Nieto").strip()
        cargo_firmante = request.POST.get("cargo_firmante", "Rector Institucional").strip()
        publicar_web = request.POST.get("publicado_web") == "on"

        comunicado = ComunicadoOficial.objects.create(
            tipo=tipo,
            numero_radicado=radicado,
            titulo=titulo,
            asunto=asunto,
            destinatario=destinatario,
            cuerpo_html=cuerpo_html,
            resumen_whatsapp=resumen_whatsapp,
            firmado_por=firmado_por,
            cargo_firmante=cargo_firmante,
            publicado_web=publicar_web,
        )

        messages.success(request, f"Documento oficial '{comunicado.numero_radicado}' guardado con éxito.")
        return redirect("admin:despacho_detalle", comunicado_id=comunicado.id)

    def analitica_view(self, request):
        from django.template.response import TemplateResponse
        from core.analitica_service import obtener_metricas_analitica

        try:
            periodo = int(request.GET.get("periodo", 3))
        except (ValueError, TypeError):
            periodo = 3
        if periodo not in (1, 2, 3, 4):
            periodo = 3

        forzar = request.GET.get("forzar") == "1"
        metricas = obtener_metricas_analitica(periodo=periodo, forzar=forzar)

        context = {
            **self.each_context(request),
            "title": "Business Intelligence & Analítica Escolar",
            "subtitle": f"Período {periodo} · Diagnóstico Institucional SERC",
            "metricas": metricas,
            "periodo_seleccionado": periodo,
        }
        return TemplateResponse(request, "admin/analitica.html", context)

    def analitica_explicar_api(self, request):
        import json
        from django.http import JsonResponse
        from core.analitica_service import generar_diagnostico_ia, obtener_metricas_analitica

        try:
            data = json.loads(request.body.decode("utf-8")) if request.body else {}
        except Exception:
            data = {}

        tipo = data.get("tipo", "general")
        try:
            periodo = int(data.get("periodo", 3))
        except (ValueError, TypeError):
            periodo = 3

        diagnostico = generar_diagnostico_ia(tipo=tipo, periodo=periodo)
        return JsonResponse({"diagnostico": diagnostico})

    def analitica_datos_api(self, request):
        from django.http import JsonResponse
        from core.analitica_service import obtener_metricas_analitica

        try:
            periodo = int(request.GET.get("periodo", 3))
        except (ValueError, TypeError):
            periodo = 3

        forzar = request.GET.get("forzar") == "1"
        metricas = obtener_metricas_analitica(periodo=periodo, forzar=forzar)
        return JsonResponse(metricas)

    # =======================================================================
    #  Inicio del panel: dashboard "Vista General" (diseño Stitch).
    #  Todos los números son REALES (de la base), no maquetas.
    # =======================================================================
    def index(self, request, extra_context=None):
        extra_context = {**(extra_context or {}), **self._dashboard_context()}
        return super().index(request, extra_context)

    def _dashboard_context(self):
        from core.models import Curso, Documento, Guia, Imagen, Materia, Noticia, Video

        hoy = timezone.localdate()
        inicio_mes = hoy.replace(day=1)

        # --- Tarjetas KPI (conteos reales) ---
        total_guias = Documento.objects.filter(categoria="guia").count()
        guias_este_mes = Documento.objects.filter(categoria="guia", fecha__gte=inicio_mes).count()
        kpis = [
            {
                "label": "Cursos", "icon": "school", "tone": "primary",
                "value": Curso.objects.count(),
                "sub_icon": "menu_book",
                "sub": f"{Materia.objects.count()} materias",
            },
            {
                "label": "Guías de estudio", "icon": "description", "tone": "tertiary",
                "value": total_guias,
                "sub_icon": "trending_up",
                "sub": f"{Documento.objects.filter(anio=2026).count()} guías 2026",
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
            {"label": "Analítica y BI Escolar", "icon": "analytics", "tone": "primary",
             "url": reverse("admin:analitica")},
            {"label": "Carga Masiva de Guías", "icon": "auto_awesome", "tone": "primary",
             "url": reverse("admin:core_documento_carga_masiva")},
            {"label": "Nuevo usuario", "icon": "person_add", "tone": "secondary",
             "url": reverse("admin:auth_user_add")},
            {"label": "Publicar noticia", "icon": "post_add", "tone": "tertiary",
             "url": reverse("admin:core_noticia_add")},
            {"label": "Subir imagen", "icon": "add_photo_alternate", "tone": "secondary",
             "url": reverse("admin:core_imagen_add")},
            {"label": "Personalizar Colores", "icon": "palette", "tone": "muted",
             "url": reverse("admin:core_configuracionapariencia_changelist")},
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
        analitica_url = reverse("admin:analitica")
        datasets_url = reverse("admin:analitica_datasets")
        despacho_url = reverse("admin:despacho_circulares")
        sections_config = [
            {
                'name': 'DESPACHO RECTORAL & CIRCULARES',
                'app_label': 'despacho_rectoral',
                'app_url': despacho_url,
                'has_module_perms': True,
                'custom_models': [
                    {
                        'name': 'Redactor Oficial de Circulares y Resoluciones',
                        'object_name': 'RedactorCirculares',
                        'admin_url': despacho_url,
                        'view_only': True,
                    }
                ],
                'models_keys': [
                    'core.ComunicadoOficial',
                ]
            },
            {
                'name': 'BUSINESS INTELLIGENCE & ANALÍTICA',
                'app_label': 'inteligencia_analitica',
                'app_url': analitica_url,
                'has_module_perms': True,
                'custom_models': [
                    {
                        'name': 'Rendimiento y Semáforo SERC',
                        'object_name': 'Analitica',
                        'admin_url': analitica_url,
                        'view_only': True,
                    },
                    {
                        'name': 'Analizador de Datasets y Pruebas Externas',
                        'object_name': 'DatasetsAnalisis',
                        'admin_url': datasets_url,
                        'view_only': True,
                    }
                ],
                'models_keys': []
            },
            {
                'name': 'SEGUIMIENTO ACADÉMICO SERC',
                'app_label': 'seguimiento_academico',
                'app_url': '#',
                'has_module_perms': True,
                'models_keys': [
                    'core.Estudiante',
                    'core.InformeValorativo',
                    'core.DatasetAnalisis',
                ]
            },
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
                    'core.Documento',
                    'core.Imagen',
                    'core.Noticia',
                    'core.Seccion',
                    'core.Video',
                    'core.ConfiguracionApariencia',
                ]
            }
        ]

        # Construimos la nueva lista de aplicaciones agrupadas
        new_app_list = []
        for sec in sections_config:
            section_models = []
            if 'custom_models' in sec:
                section_models.extend(sec['custom_models'])
            for m_key in sec.get('models_keys', []):
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
