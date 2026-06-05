"""
Carga la identidad institucional REAL de la I.E.D. CEIS
(Complejo Educativo Integral Sopó, Cundinamarca) y sus 18 secciones/proyectos.

- Identidad de la home (nombre, lema, misión, visión, contacto): texto verbatim.
- 18 páginas (El Colegio + Proyectos): se cargan desde core/data/iedceis_paginas.json,
  generado a partir del sitio oficial. No se inventa contenido.

Idempotente: actualiza si ya existen.

    python manage.py seed_iedceis
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from core.models import Seccion, Video

# Texto verbatim del sitio oficial.
MISION = (
    "La IED Complejo Educativo Integral Sopó (CEIS) contribuye de manera misional al "
    "desarrollo de la dimensión humana, trabajando para que las personas alcancen su "
    "desarrollo integral y la autonomía a través de la implementación del sistema educativo "
    "relacional Cundinamarca. La institución propone contribuir en la formación integral de "
    "los estudiantes prestando un servicio educativo de calidad, desarrollando el potencial "
    "de interacción y creación de los seres humanos para que sean agentes de transformación "
    "de sí mismos y de su entorno, mejoren su calidad de vida, bienestar y aporten al "
    "desarrollo del país."
)

VISION = (
    "Para el año 2026 la IED Complejo Educativo Integral Sopó (CEIS) busca ser una "
    "institución educativa moderna, dinámica y altamente competitiva, posicionada por encima "
    "de los estándares nacionales, por medio de procesos de enseñanza innovadores, inclusivos "
    "y efectivos, una didáctica adecuada y una metodología enfocada en el aprendizaje "
    "significativo y desarrollo de la autonomía, contando con profesionales comprometidos en "
    "el proceso de aprendizaje de sus estudiantes, aulas especializadas y herramientas de "
    "tecnología actualizadas, con estudiantes con sentido de vida, motivados en ser líderes "
    "comunitarios, productivos e inspiradores de progreso sostenible."
)

CONTACTO = (
    "Cel./WhatsApp 3108710141 · iedceis@gmail.com · Carrera 10 No. 1-31, Sopó, Cundinamarca · "
    "Atención presencial secretaría académica: martes, miércoles y jueves de 8:00 a.m. a 12:00 m."
)

# Identidad de la home (categoría HOME: no se lista, alimenta la portada).
IDENTIDAD = {
    "nombre_sitio": ("I.E.D. CEIS", "Complejo Educativo Integral Sopó"),
    "lema": ("Lema", "Paz, Educación, Progreso"),
    "mision": ("Misión", MISION),
    "vision": ("Visión", VISION),
    "contacto": ("Contacto", CONTACTO),
}

RUTA_PAGINAS = Path(__file__).resolve().parents[2] / "data" / "iedceis_paginas.json"


class Command(BaseCommand):
    help = "Carga la identidad y las 18 secciones reales de la I.E.D. CEIS (idempotente)."

    def handle(self, *args, **opciones):
        # 1) Identidad de la home.
        for clave, (titulo, contenido) in IDENTIDAD.items():
            Seccion.objects.update_or_create(
                clave=clave,
                defaults={"titulo": titulo, "contenido": contenido,
                          "categoria": Seccion.Categoria.HOME, "orden": 0})

        # 2) Las 18 páginas (El Colegio + Proyectos) desde el JSON del sitio.
        paginas = json.loads(RUTA_PAGINAS.read_text(encoding="utf-8"))
        for clave, p in paginas.items():
            Seccion.objects.update_or_create(
                clave=clave,
                defaults={"titulo": p["titulo"], "contenido": p["contenido"],
                          "categoria": p["categoria"], "orden": p["orden"]})

        # 3) Quitar el video demo de relleno (rickroll), impropio de un sitio real.
        borrados = Video.objects.filter(youtube_url__contains="dQw4w9WgXcQ").delete()[0]

        col = Seccion.objects.filter(categoria=Seccion.Categoria.COLEGIO).count()
        pro = Seccion.objects.filter(categoria=Seccion.Categoria.PROYECTO).count()
        self.stdout.write(self.style.SUCCESS(
            "Identidad + secciones cargadas: %d en 'El Colegio', %d en 'Proyectos'. "
            "Videos demo quitados: %d." % (col, pro, borrados)))
