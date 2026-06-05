from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Núcleo: modelos compartidos y lógica común de Athena."""
    default_auto_field = "django.db.models.BigAutoField"
    name = "core"
    verbose_name = "Núcleo (datos del colegio)"
