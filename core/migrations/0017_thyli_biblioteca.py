from django.db import migrations


def aplicar(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")

    # Crear o actualizar sección THYLI
    Seccion.objects.update_or_create(
        clave="thyli",
        defaults={
            "titulo": "THYLI · Gestión Bibliotecaria",
            "enlace_externo": "https://biblioteca-proyecto-d64cb.web.app/buscar.html",
            "categoria": "software",
            "grupo": "Gestión Bibliotecaria Escolar",
            "orden": 12,
            "contenido": (
                "T.H.Y.L.I es el sistema web para la administración y circulación bibliotecaria de la "
                "I.E.D. Complejo Educativo Integral Sopó (C.E.I.S).\n\n"
                "Qué permite hacer: catálogo interactivo de libros para estudiantes y docentes, préstamos con "
                "verificación visual de carnet estudiantil, escaneo inalámbrico mediante código QR y consulta de "
                "disponibilidad en tiempo real.\n\n"
                "Para quién: estudiantes, docentes y administración bibliotecaria."
            ),
        },
    )


def revertir(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    Seccion.objects.filter(clave="thyli").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0016_tecnoalimentaria"),
    ]
    operations = [
        migrations.RunPython(aplicar, revertir),
    ]
