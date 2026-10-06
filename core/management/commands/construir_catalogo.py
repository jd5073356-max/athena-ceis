"""
Construye el catálogo académico (Año → Período → Curso → Materia → Guía) a
partir de los Documento de categoría 'guia' que ya están cargados en GCS.
Reutiliza el mismo archivo (no vuelve a subir): cada Guía apunta a la ruta de
GCS del Documento original.

    python manage.py construir_catalogo --reset

- Períodos: 1, 2, 3, 4
- Cursos: Prejardín, Jardín, Transición, 1° … 11° (grado general, sin secciones)
- Materias: forma corta (P. Matemático, P. Científico, …)
- Guías: el título real de cada guía
"""
import re

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import Anio, Curso, Documento, Guia, Materia, Periodo
from core.management.commands.importar_documentos import _normalizar_area, _sin_acentos

_PERIODO_NUM = {"I": 1, "II": 2, "III": 3, "IV": 4}

_AREA_CORTA = {
    "Comunicaciones": "Comunicaciones",
    "Inglés": "Inglés",
    "Pensamiento Matemático": "P. Matemático",
    "Pensamiento Científico": "P. Científico",
    "Pensamiento Social": "P. Social",
    "Pensamiento Artístico": "P. Artístico",
    "Pensamiento Ético y Ciudadano": "P. Ético y Ciudadano",
    "Pensamiento Tecnológico": "P. Tecnológico",
    "Cultura Física y Deportiva": "Cultura Física",
}


def _grado(d) -> str:
    """Etiqueta de curso (grado general): Prejardín/Jardín/Transición/1°…11°."""
    g = (d.grado or "").strip()
    if g:
        m = re.match(r"(\d+)", g)
        if m:
            return f"{int(m.group(1))}°"
        gl = _sin_acentos(g).lower()
        if "prejard" in gl:
            return "Prejardín"
        if "jard" in gl:
            return "Jardín"
        if "transici" in gl:
            return "Transición"
        return g
    m = re.search(r"\b(1[01]|[2-9])\s*[°º]", d.titulo)
    if m:
        return f"{int(m.group(1))}°"
    return "General"


def _materia(d) -> str:
    area = d.area or _normalizar_area(d.titulo)
    return _AREA_CORTA.get(area, "General")


class Command(BaseCommand):
    help = "Construye el catálogo Año→Período→Curso→Materia→Guía desde los Documento."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true",
                            help="Borra el catálogo actual (Años y todo lo que cuelga) antes de construir.")

    @transaction.atomic
    def handle(self, *args, **o):
        if o["reset"]:
            n = Anio.objects.count()
            Anio.objects.all().delete()  # cascada: períodos, cursos, materias, guías
            self.stdout.write(f"--reset: borrados {n} años y todo su árbol.")

        guias = (Documento.objects.filter(categoria="guia")
                 .exclude(titulo__iexact="prueba1").exclude(anio__isnull=True))

        c_anio, c_per, c_cur, c_mat = {}, {}, {}, {}

        def anio_obj(y):
            if y not in c_anio:
                obj, created = Anio.objects.get_or_create(anio=y, defaults={"activo": True})
                c_anio[y] = obj
            return c_anio[y]

        def per_obj(a, num):
            k = (a.pk, num)
            if k not in c_per:
                obj, created = Periodo.objects.get_or_create(anio=a, numero=num)
                c_per[k] = obj
            return c_per[k]

        def cur_obj(p, nombre, nivel):
            k = (p.pk, nombre)
            if k not in c_cur:
                obj, created = Curso.objects.get_or_create(periodo=p, nombre=nombre, defaults={"nivel": nivel})
                c_cur[k] = obj
            return c_cur[k]

        def mat_obj(c, nombre):
            k = (c.pk, nombre)
            if k not in c_mat:
                obj, created = Materia.objects.get_or_create(curso=c, nombre=nombre)
                c_mat[k] = obj
            return c_mat[k]

        total = 0
        for d in guias.iterator():
            a = anio_obj(d.anio)
            p = per_obj(a, _PERIODO_NUM.get(d.periodo, 1))
            cur = cur_obj(p, _grado(d), (d.nivel or "").title())
            mat = mat_obj(cur, _materia(d))
            g = Guia(materia=mat, titulo=d.titulo[:160])
            g.archivo.name = d.archivo.name  # reutiliza el objeto ya en GCS
            g.save()
            total += 1
            if total % 100 == 0:
                self.stdout.write(f"  ... {total} guías")

        self.stdout.write(self.style.SUCCESS(
            f"Catálogo construido. Años: {Anio.objects.count()}, Períodos: {Periodo.objects.count()}, "
            f"Cursos: {Curso.objects.count()}, Materias: {Materia.objects.count()}, Guías: {Guia.objects.count()}."))
