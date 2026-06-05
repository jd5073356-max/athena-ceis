from django.contrib import admin

class AthenaAdminSite(admin.AdminSite):
    site_header = "Athena · Panel del Rector"
    site_title = "Athena"
    index_title = "Gestión del sitio del colegio"

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
