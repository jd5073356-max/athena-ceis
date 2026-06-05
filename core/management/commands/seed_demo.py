"""
Carga datos de ejemplo para ver Athena funcionando de inmediato.

Crea la jerarquía 2026 → Período 1 → 6°A → Matemáticas → una guía (PDF),
más secciones de texto, una noticia, un video y una imagen.

Es idempotente: se puede correr varias veces sin duplicar.

    python manage.py seed_demo
"""
import base64

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models import (
    Anio, Curso, Guia, Imagen, Materia, Noticia, Periodo, Seccion, Video,
)

# PDF mínimo válido (empieza con %PDF, suficiente para abrir y validar).
PDF_DEMO = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 300 144]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
    b"%%EOF\n"
)

# PNG 1x1 transparente (válido para el validador de imágenes).
PNG_DEMO = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYPhfDwAChwGA"
    "60e6kgAAAABJRU5ErkJggg=="
)


class Command(BaseCommand):
    help = "Carga datos de ejemplo (idempotente)."

    def handle(self, *args, **opciones):
        # --- Secciones de texto de la home ---------------------------------
        secciones = {
            "nombre_sitio": ("Nombre del Colegio", "Edita este texto desde el panel del rector."),
            "lema": ("Lema", "Bienvenidos a nuestra comunidad educativa."),
            "mision": ("Misión", "Texto de la misión institucional (editable por el rector)."),
            "vision": ("Visión", "Texto de la visión institucional (editable por el rector)."),
            "contacto": ("Contacto", "Dirección, teléfono y correo del colegio."),
        }
        for clave, (titulo, contenido) in secciones.items():
            Seccion.objects.get_or_create(
                clave=clave, defaults={"titulo": titulo, "contenido": contenido})

        # --- Jerarquía de guías --------------------------------------------
        anio, _ = Anio.objects.get_or_create(anio=2026, defaults={"activo": True})
        periodo, _ = Periodo.objects.get_or_create(
            anio=anio, numero=1, defaults={"nombre": "Primer período"})
        curso, _ = Curso.objects.get_or_create(
            periodo=periodo, nombre="6°A", defaults={"nivel": "Secundaria"})
        materia, _ = Materia.objects.get_or_create(curso=curso, nombre="Matemáticas")

        if not Guia.objects.filter(materia=materia, titulo="Guía 1 — Números enteros").exists():
            guia = Guia(
                materia=materia,
                titulo="Guía 1 — Números enteros",
                descripcion="Repaso de operaciones con números enteros.",
            )
            guia.archivo.save("guia-1-numeros-enteros.pdf", ContentFile(PDF_DEMO), save=True)

        # --- Noticia, video, imagen ----------------------------------------
        Noticia.objects.get_or_create(
            titulo="Bienvenida al año escolar 2026",
            defaults={"cuerpo": "Damos la bienvenida a toda la comunidad educativa al nuevo año."})

        Video.objects.get_or_create(
            titulo="Video institucional",
            defaults={
                "youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "descripcion": "Presentación del colegio.",
            })

        if not Imagen.objects.filter(titulo="Foto de ejemplo").exists():
            img = Imagen(titulo="Foto de ejemplo")
            img.archivo.save("ejemplo.png", ContentFile(PNG_DEMO), save=True)

        self.stdout.write(self.style.SUCCESS(
            "Datos de ejemplo cargados. Entra al panel en /admin/ y a la web en /."))
