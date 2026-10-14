from django.db import migrations

def actualizar_titulos_grupos(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    # EduPass con grupo Gestión Escolar
    Seccion.objects.filter(clave="edupass").update(
        titulo="EduPass",
        grupo="Asistencia Escolar QR"
    )
    # BDEI y ATDIE en INCLUSION
    Seccion.objects.filter(clave="bdei").update(
        titulo="B.A.D.E.I (Boletines)",
        grupo="Inclusión Educativa"
    )
    Seccion.objects.filter(clave="atdie").update(
        titulo="ATDIE (Inventario)",
        grupo="Inclusión Educativa"
    )
    Seccion.objects.filter(clave="eco-inclusivo").update(
        titulo="Eco Inclusivo",
        grupo="Inclusión Educativa"
    )

def revertir(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0014_actualizar_categoria_software"),
    ]
    operations = [
        migrations.RunPython(actualizar_titulos_grupos, revertir),
    ]
