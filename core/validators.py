"""
Validadores de archivos subidos por el rector.

Doble verificación: extensión + firma binaria (magic bytes). Así una imagen
renombrada a .pdf (o al revés) no pasa el filtro.

- Las guías solo aceptan PDF.
- La galería solo acepta imágenes (jpg, png, gif, webp).
"""
import os
from django.core.exceptions import ValidationError

EXTENSIONES_PDF = {".pdf"}
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


def _leer_firma(archivo, n: int = 12) -> bytes:
    """Lee los primeros n bytes del archivo y deja el cursor donde estaba."""
    try:
        posicion = archivo.tell()
    except (AttributeError, OSError):
        posicion = 0
    archivo.seek(0)
    firma = archivo.read(n)
    archivo.seek(posicion)
    return firma or b""


def validar_pdf(archivo):
    """Acepta solo PDFs reales (extensión .pdf + cabecera %PDF)."""
    nombre = getattr(archivo, "name", "") or ""
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_PDF:
        raise ValidationError("La guía debe ser un archivo PDF (.pdf).")
    if not _leer_firma(archivo, 5).startswith(b"%PDF"):
        raise ValidationError("El archivo no es un PDF válido.")


def validar_imagen(archivo):
    """Acepta solo imágenes reales (jpg, png, gif, webp)."""
    nombre = getattr(archivo, "name", "") or ""
    extension = os.path.splitext(nombre)[1].lower()
    if extension not in EXTENSIONES_IMAGEN:
        raise ValidationError("La imagen debe ser .jpg, .jpeg, .png, .gif o .webp.")
    firma = _leer_firma(archivo, 12)
    es_valida = (
        firma[:3] == b"\xff\xd8\xff"                       # JPEG
        or firma.startswith(b"\x89PNG\r\n\x1a\n")          # PNG
        or firma[:6] in (b"GIF87a", b"GIF89a")             # GIF
        or (firma[:4] == b"RIFF" and firma[8:12] == b"WEBP")  # WEBP
    )
    if not es_valida:
        raise ValidationError("El archivo no es una imagen válida.")
