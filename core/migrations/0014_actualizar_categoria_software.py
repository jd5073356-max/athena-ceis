from django.db import migrations

SOFTWARE_KEYS = ["bdei", "eco-inclusivo", "edupass", "atdie"]

def migrar_a_software(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    Seccion.objects.filter(clave__in=SOFTWARE_KEYS).update(categoria="software")

def revertir_a_proyecto(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    Seccion.objects.filter(clave__in=SOFTWARE_KEYS).update(categoria="proyecto")

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0013_seccion_categoria_software"),
    ]
    operations = [
        migrations.RunPython(migrar_a_software, revertir_a_proyecto),
    ]
