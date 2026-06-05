from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class PanelRectorConfig(AppConfig):
    """Panel del Rector: personalización del Django Admin."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "panel_rector"
    verbose_name = "Panel del Rector"


class AthenaAdminConfig(AdminConfig):
    default_site = "panel_rector.admin_site.AthenaAdminSite"
