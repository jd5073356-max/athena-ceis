"""
Importa las guías SERC, horarios y formatos del Drive del colegio como
registros Documento (suben a GCS), preservando la jerarquía real del Drive:

    GUÍAS  ->  Año / Nivel / (Grado) / Período / Área / archivo.pdf
    HORARIOS, FORMATOS  ->  sueltos por categoría

El nombre de cada área se normaliza a las áreas canónicas del SERC (se unifican
las muchas grafías de la misma materia). El objeto en GCS se guarda en una ruta
jerárquica para que no colisionen archivos con el mismo nombre. Idempotente.

    python manage.py importar_documentos                 # años por defecto
    python manage.py importar_documentos --reset         # purga lo importado antes
    python manage.py importar_documentos --years 2025 2026
"""
import concurrent.futures
import os
import re
import threading
import unicodedata
from pathlib import Path

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.management.base import BaseCommand

from core.models import Documento

AÑOS_POR_DEFECTO = [2023, 2024, 2025, 2026]
# Categorías que crea este importador (las que purga --reset).
CATS_IMPORTADAS = ["guia", "horario", "formato", "otro"]


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", _sin_acentos(s)).strip("-").lower()
    return s or "_"


def _cap_key(key: str, limite: int = 230) -> str:
    """Acorta el nombre del archivo si la ruta supera el max_length del campo
    (upload_to='documentos/' aún antepone ~11 caracteres)."""
    if len(key) <= limite:
        return key
    carpeta, _, nombre = key.rpartition("/")
    stem, ext = os.path.splitext(nombre)
    stem = stem[:max(8, len(stem) - (len(key) - limite))]
    return f"{carpeta}/{stem}{ext}"


# Reglas de normalización de área (subcadena sin acentos, en orden de prioridad).
_REGLAS_AREA = [
    ("cultura fisica", "Cultura Física y Deportiva"),
    ("fisica y deport", "Cultura Física y Deportiva"),
    ("ed fisica", "Cultura Física y Deportiva"),
    ("ed. fisica", "Cultura Física y Deportiva"),
    ("deportiv", "Cultura Física y Deportiva"),
    ("comunicacion", "Comunicaciones"),
    ("castellano", "Comunicaciones"),
    ("lengua", "Comunicaciones"),
    ("ingl", "Inglés"),
    ("geometr", "Pensamiento Matemático"),
    ("estadist", "Pensamiento Matemático"),
    ("trigonometr", "Pensamiento Matemático"),
    ("calculo", "Pensamiento Matemático"),
    ("matemat", "Pensamiento Matemático"),
    ("quimic", "Pensamiento Científico"),
    ("biolog", "Pensamiento Científico"),
    ("ciencias natural", "Pensamiento Científico"),
    ("cientific", "Pensamiento Científico"),
    ("fisica", "Pensamiento Científico"),
    ("artistic", "Pensamiento Artístico"),
    ("tecnolog", "Pensamiento Tecnológico"),
    ("informatic", "Pensamiento Tecnológico"),
    ("politic", "Pensamiento Social"),
    ("economic", "Pensamiento Social"),
    ("social", "Pensamiento Social"),
    ("filosof", "Pensamiento Ético y Ciudadano"),
    ("religios", "Pensamiento Ético y Ciudadano"),
    ("etic", "Pensamiento Ético y Ciudadano"),
    ("ciudadan", "Pensamiento Ético y Ciudadano"),
    ("moral", "Pensamiento Ético y Ciudadano"),
]


def _normalizar_area(seg: str) -> str:
    t = _sin_acentos(seg).lower()
    for clave, valor in _REGLAS_AREA:
        if clave in t:
            return valor
    return seg.strip().title()


def _parsear_guia(parts):
    """Extrae (anio, nivel, grado, periodo, area) de los segmentos de carpeta."""
    anio = nivel = periodo = grado = None
    candidatos_area = []
    for seg in parts:
        n = seg.strip()
        u = _sin_acentos(n).upper()
        if re.search(r"GU[IÍ]AS\s*20\d{2}", n, re.I) or re.fullmatch(r"20\d{2}", n):
            anio = int(re.search(r"20\d{2}", n).group())
        elif "BACHILLER" in u:
            nivel = "bachillerato"
        elif "PRIMARIA" in u:
            nivel = "primaria"
        elif "PREESCOLAR" in u:
            nivel = "preescolar"
        elif "PERI" in u and re.match(r"^(IV|III|II|I)\b", u):
            periodo = re.match(r"^(IV|III|II|I)", u).group(1)
        elif re.match(r"^\d+\s*[º°]", n) or re.search(r"(transici|jard)", n, re.I):
            grado = n
        else:
            candidatos_area.append(n)
    area = _normalizar_area(candidatos_area[0]) if candidatos_area else ""
    if not nivel:
        if grado and re.match(r"^[1-5]", grado):
            nivel = "primaria"
        elif grado:
            nivel = "preescolar"
        else:
            nivel = "bachillerato"
    return anio, nivel, (grado or ""), (periodo or ""), area


class Command(BaseCommand):
    help = "Importa guías/horarios/formatos del Drive como Documento (suben a GCS), con jerarquía."

    def add_arguments(self, parser):
        parser.add_argument("--source", default="/home/juan/iedceis_drive")
        parser.add_argument("--years", nargs="+", type=int, default=AÑOS_POR_DEFECTO)
        parser.add_argument("--reset", action="store_true",
                            help="Borra los Documento ya importados (y sus objetos en GCS) antes de importar.")
        parser.add_argument("--keep", nargs="+", default=["prueba1"],
                            help="Títulos a preservar al hacer --reset (subidas manuales).")
        parser.add_argument("--workers", type=int, default=8,
                            help="Hilos de subida concurrente a GCS.")

    def _guardar(self, f: Path, *, categoria, anio, nivel="", grado="", periodo="", area="", key):
        titulo = f.stem.strip()
        if Documento.objects.filter(categoria=categoria, anio=anio, nivel=nivel,
                                    grado=grado, periodo=periodo, area=area, titulo=titulo).exists():
            return False
        doc = Documento(titulo=titulo, categoria=categoria, anio=anio,
                        nivel=nivel, grado=grado, periodo=periodo, area=area)
        with open(f, "rb") as fh:
            doc.archivo.save(_cap_key(key), ContentFile(fh.read()), save=True)
        return True

    def handle(self, *args, **o):
        src = Path(o["source"])
        years = set(o["years"])
        if not src.is_dir():
            self.stdout.write(self.style.ERROR(f"No existe la fuente {src}")); return

        if o["reset"]:
            keep = [k.lower() for k in o["keep"]]
            qs = Documento.objects.filter(categoria__in=CATS_IMPORTADAS)
            borrados = 0
            for d in qs:
                if d.titulo.lower() in keep:
                    continue
                try:
                    d.archivo.delete(save=False)
                except Exception:
                    pass
                d.delete(); borrados += 1
            self.stdout.write(f"--reset: {borrados} documentos previos borrados "
                              f"(preservados: {', '.join(o['keep'])}).")

        padres = src / "padres"
        guias_root = padres / "guias_serc_ceis"

        # 1) Construir la lista de tareas (sin red todavía).
        tareas = []
        for anio_dir in sorted(guias_root.glob("*")):
            if not anio_dir.is_dir():
                continue
            m = re.search(r"20\d{2}", anio_dir.name)
            if not m or int(m.group()) not in years:
                continue
            for f in sorted(anio_dir.rglob("*")):
                if not f.is_file() or f.name.startswith("."):
                    continue
                anio, nivel, grado, periodo, area = _parsear_guia(f.relative_to(guias_root).parts[:-1])
                key = "/".join([str(anio or "sa"), nivel or "_", _slug(grado),
                                periodo or "_", _slug(area)]) + "/" + f.name
                tareas.append(dict(f=f, categoria="guia", anio=anio, nivel=nivel,
                                   grado=grado, periodo=periodo, area=area, key=key))

        for carpeta, categoria, anio in [
            (padres / "Horarios clases 2026", "horario", 2026),
            (padres / "Formato para docentes", "formato", None),
            (padres / "Formatos para permisos de estudiantes", "formato", None),
        ]:
            if not carpeta.is_dir():
                continue
            for f in sorted(carpeta.rglob("*")):
                if not f.is_file() or f.name.startswith("."):
                    continue
                tareas.append(dict(f=f, categoria=categoria, anio=anio,
                                   key=f"{categoria}/{_slug(carpeta.name)}/{f.name}"))

        # 2) Subir en paralelo (cada hilo usa su propia conexión a la BD).
        default_storage.exists("__warmup__")  # inicializa el cliente GCS en el hilo principal
        workers = o["workers"]
        self.stdout.write(f"{len(tareas)} archivos candidatos. Subiendo con {workers} hilos...")
        cont = {"ok": 0, "skip": 0, "err": 0}
        lock = threading.Lock()

        def trabajar(t):
            try:
                creado = self._guardar(**t)
                with lock:
                    cont["ok" if creado else "skip"] += 1
            except Exception as e:
                with lock:
                    cont["err"] += 1
                self.stderr.write(f"  ERROR {t['f'].name}: {e}")
            with lock:
                hechos = cont["ok"] + cont["skip"] + cont["err"]
                if hechos % 50 == 0:
                    self.stdout.write(f"  ... {hechos}/{len(tareas)} (nuevos {cont['ok']})")

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            list(ex.map(trabajar, tareas))

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Nuevos: {cont['ok']}, ya estaban: {cont['skip']}, errores: {cont['err']}. "
            f"Total en DB: {Documento.objects.count()}"))
