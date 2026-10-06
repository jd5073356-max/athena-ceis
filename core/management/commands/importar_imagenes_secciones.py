"""
Importa las imágenes de static/secciones/<clave>/ como registros Imagen,
asociados a su Sección, para que el rector las gestione desde el admin.
Idempotente a nivel de sección (si ya tiene imágenes, la omite).

    python manage.py importar_imagenes_secciones
"""
import os
from pathlib import Path

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from core.models import Imagen, Seccion

_EXTS = (".webp", ".jpg", ".jpeg", ".png", ".gif")


class Command(BaseCommand):
    help = "Importa las imágenes de las secciones (static/secciones) al modelo Imagen."

    def handle(self, *args, **opciones):
        base = Path(settings.BASE_DIR) / "static" / "secciones"
        if not base.is_dir():
            self.stdout.write("No existe static/secciones."); return

        # Sección contenedora de la galería de la home.
        Seccion.objects.get_or_create(clave="inicio", defaults={
            "titulo": "Inicio (galería)", "contenido": "", "categoria": "home", "orden": 99})

        total = 0
        for carpeta in sorted(base.iterdir()):
            if not carpeta.is_dir():
                continue
            seccion = Seccion.objects.filter(clave=carpeta.name).first()
            if not seccion:
                self.stdout.write(f"  (sin sección '{carpeta.name}', omitida)"); continue
            if seccion.imagenes.exists():
                continue  # ya importada
            archivos = sorted(f for f in os.listdir(carpeta) if f.lower().endswith(_EXTS))
            for i, nombre in enumerate(archivos):
                img = Imagen(seccion=seccion, titulo=f"{seccion.titulo} — {i + 1}", orden=i)
                with open(carpeta / nombre, "rb") as fh:
                    img.archivo.save(nombre, ContentFile(fh.read()), save=True)
                total += 1
            self.stdout.write(f"  {seccion.clave}: {len(archivos)} imágenes")

        self.stdout.write(self.style.SUCCESS(
            f"Importadas {total} imágenes. Total Imagen en DB: {Imagen.objects.count()}"))
