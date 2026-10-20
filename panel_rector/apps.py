from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class PanelRectorConfig(AppConfig):
    """Panel Administrativo: personalización del Django Admin."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "panel_rector"
    verbose_name = "Panel Administrativo"


class AthenaAdminConfig(AdminConfig):
    default_site = "panel_rector.admin_site.AthenaAdminSite"
