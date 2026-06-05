from django.apps import AppConfig


class WebPublicaConfig(AppConfig):
    """Sitio público: lo que ven padres y estudiantes."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "web_publica"
    verbose_name = "Web pública"
