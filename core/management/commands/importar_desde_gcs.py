import re
import unicodedata
from django.core.management.base import BaseCommand, CommandError
from core.models import Documento


AREA_MAP = {
    "comunicaciones": "Comunicaciones",
    "cultura-fisica-y-deportiva": "Cultura Física y Deportiva",
    "ingles": "Inglés",
    "pensamiento-artistico": "Pensamiento Artístico",
    "pensamiento-cientifico": "Pensamiento Científico",
    "pensamiento-etico-y-ciudadano": "Pensamiento Ético y Ciudadano",
    "pensamiento-matematico": "Pensamiento Matemático",
    "pensamiento-social": "Pensamiento Social",
    "pensamiento-tecnologico": "Pensamiento Tecnológico",
}


def _sin_acentos(s):
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _titulo_desde(filename):
    stem = filename.rsplit(".", 1)[0] if "." in filename else filename
    stem = stem.replace("_", " ").replace("-", " ").strip()
    stem = re.sub(r"\s+", " ", stem)
    return stem[:200]


class Command(BaseCommand):
    help = "Crea registros Documento desde archivos ya existentes en GCS bucket athena-media-ceis"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Solo mostrar qué se crearía")

    def handle(self, *args, **options):
        try:
            from google.cloud import storage
        except ImportError:
            raise CommandError("google-cloud-storage no instalado")

        client = storage.Client()
        bucket = client.bucket("athena-media-ceis")

        blobs = list(bucket.list_blobs(prefix="documentos/"))
        archivos = [b for b in blobs if not b.name.endswith("/")]

        creados = 0
        existentes = 0
        saltados = 0

        for blob in archivos:
            path = blob.name

            meta = self._parse(path)
            if meta is None:
                self.stdout.write(f"  ? saltado (no clasificado): {path}")
                saltados += 1
                continue

            if options["dry_run"]:
                self.stdout.write(f"  [dry] {meta['categoria']} → {meta['titulo']}")
                creados += 1
                continue

            if Documento.objects.filter(archivo=path).exists():
                existentes += 1
                continue

            doc = Documento(anio=meta.get("anio"), nivel=meta.get("nivel", ""),
                            grado=meta.get("grado", ""), periodo=meta.get("periodo", ""),
                            area=meta.get("area", ""), titulo=meta["titulo"],
                            categoria=meta["categoria"])
            doc.archivo = path
            doc.save()
            creados += 1

            if creados % 50 == 0:
                self.stdout.write(f"  ... {creados} creados, {existentes} existentes")

        self.stdout.write(self.style.SUCCESS(
            f"Listo. Creados: {creados}, ya existían: {existentes}, sin clasificar: {saltados}"))

    def _parse(self, path):
        parts = path.split("/")
        if parts[0] != "documentos" or len(parts) < 2:
            return None

        if len(parts) == 2:
            return self._root_level(parts[1])

        if parts[1] == "formato" and len(parts) >= 4:
            return self._formato(parts)

        if parts[1] == "horario" and len(parts) >= 4:
            return self._horario(parts)

        if re.match(r"^20\d{2}$", parts[1]) and len(parts) >= 4:
            return self._guia(parts)

        return None

    def _root_level(self, filename):
        titulo = _titulo_desde(filename)
        u = _sin_acentos(titulo).upper()
        if "CIRCULAR" in u:
            cat = "circular"
        elif "MANUAL" in u or "CONVIVENCIA" in u:
            cat = "manual"
        elif "GUIA" in u or "GUÍ" in u:
            cat = "guia"
        else:
            cat = "otro"
        m = re.search(r"20\d{2}", titulo)
        anio = int(m.group()) if m else None
        return {"titulo": titulo, "categoria": cat, "anio": anio,
                "nivel": "", "grado": "", "periodo": "", "area": ""}

    def _formato(self, parts):
        filename = parts[-1]
        titulo = _titulo_desde(filename)
        return {"titulo": titulo, "categoria": "formato", "anio": None,
                "nivel": "", "grado": "", "periodo": "", "area": ""}

    def _horario(self, parts):
        filename = parts[-1]
        titulo = _titulo_desde(filename)
        return {"titulo": titulo, "categoria": "horario", "anio": 2026,
                "nivel": "", "grado": "", "periodo": "", "area": ""}

    def _guia(self, parts):
        anio = int(parts[1])
        nivel = parts[2]

        if nivel == "bachillerato":
            return self._guia_bachillerato(anio, parts)
        else:
            return self._guia_general(anio, nivel, parts)

    def _guia_bachillerato(self, anio, parts):
        if len(parts) < 7:
            return None
        grado = parts[3]
        periodo = parts[4]
        area_raw = parts[5]
        area = AREA_MAP.get(area_raw, area_raw.replace("-", " ").title())
        filename = parts[-1]
        titulo = _titulo_desde(filename)
        return {"titulo": titulo, "categoria": "guia", "anio": anio,
                "nivel": "bachillerato", "grado": grado, "periodo": periodo, "area": area}

    def _guia_general(self, anio, nivel, parts):
        if len(parts) < 7:
            return None
        grado = parts[3]
        periodo = parts[4]
        filename = parts[-1]
        titulo = _titulo_desde(filename)
        return {"titulo": titulo, "categoria": "guia", "anio": anio,
                "nivel": nivel, "grado": grado, "periodo": periodo, "area": ""}
