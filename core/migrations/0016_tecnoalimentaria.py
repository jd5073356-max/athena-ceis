from django.db import migrations


def aplicar(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")

    # Crear o actualizar sección TecnoAlimentaria
    Seccion.objects.update_or_create(
        clave="tecnoalimentaria",
        defaults={
            "titulo": "TecnoAlimentaria",
            "enlace_externo": "https://technoaliementaria.netlify.app/",
            "categoria": "software",
            "grupo": "Alimentación Escolar",
            "orden": 15,
            "contenido": (
                "TecnoAlimentaria es el sistema web para la gestión y seguimiento del servicio de "
                "alimentación escolar del SENA en el C.E.I.S."
            ),
        },
    )


def revertir(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    Seccion.objects.filter(clave="tecnoalimentaria").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0015_titulos_inclusion_edupass"),
    ]
    operations = [
        migrations.RunPython(aplicar, revertir),
    ]
