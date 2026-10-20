import os
import sys
import json
import re
import time
import unicodedata
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import boto3
import gdown
from django.utils.text import get_valid_filename

# Configurar entorno Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from django.db import connections
from core.models import Documento

CACHE_FILE = Path("/tmp/guias_2026_drive_files.json")
LOCAL_DIR_BASE = Path("/home/juan/iedceis_drive/padres/guias_serc_ceis/GUÍAS 2026")

R2_ENDPOINT = "https://2437c55c10f2f7c1dd8e879e832cd97c.r2.cloudflarestorage.com"
R2_ACCESS_KEY = "02fc89c6dbfe4f40f4a928e05aab975e"
R2_SECRET_KEY = "4aff049ec9df94700f993e0d62a42892700ec4bcecf94c023e2d25e2607cd144"
R2_BUCKET = "athena"

_REGLAS_AREA = [
    ("cultura fisica", "Cultura Física y Deportiva"),
    ("fisica y deport", "Cultura Física y Deportiva"),
    ("ed fisica", "Cultura Física y Deportiva"),
    ("ed. fisica", "Cultura Física y Deportiva"),
    ("deportiv", "Cultura Física y Deportiva"),
    ("cominucacion", "Comunicaciones"),
    ("cuminicacion", "Comunicaciones"),
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
    ("natural", "Pensamiento Científico"),
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


def _sin_acentos(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", _sin_acentos(s)).strip("-").lower()
    return s or "_"


def _cap_key(key: str, limite: int = 240) -> str:
    if len(key) <= limite:
        return key
    carpeta, _, nombre = key.rpartition("/")
    stem, ext = os.path.splitext(nombre)
    stem = stem[:max(8, len(stem) - (len(key) - limite))]
    return f"{carpeta}/{stem}{ext}"


def _normalizar_area(seg: str) -> str:
    t = _sin_acentos(seg).lower()
    for clave, valor in _REGLAS_AREA:
        if clave in t:
            return valor
    return seg.strip().title()


def parse_metadata(item):
    path = item["path"]
    parts = path.split("/")
    folder_parts = parts[:-1]
    filename = parts[-1]

    nivel = periodo = grado = ""
    candidatos_area = []

    for seg in folder_parts:
        n = seg.strip()
        u = _sin_acentos(n).upper()
        if "BACHILLER" in u:
            nivel = "bachillerato"
        elif "PRIMARIA" in u:
            nivel = "primaria"
        elif "PREESCOLAR" in u:
            nivel = "preescolar"
        elif "PERI" in u and re.search(r"\b(IV|III|II|I)\b", u):
            periodo = re.search(r"\b(IV|III|II|I)\b", u).group(1)
        elif re.search(r"^\d+\s*[º°]", n) or re.search(r"(transici|jard|prejard)", n, re.I):
            grado = n.replace("°", "º")
        else:
            candidatos_area.append(n)

    # Grado y nivel segun reglas
    if nivel == "preescolar":
        if "PREJARD" in path.upper():
            grado = "Prejardín"
        elif "JARD" in path.upper():
            grado = "Jardín"
        else:
            grado = "Transición"
    elif nivel == "primaria":
        if not grado:
            m = re.search(r"\b([1-5])[\s°º\.]*", path)
            grado = f"{m.group(1)}º" if m else ""
    elif nivel == "bachillerato":
        # En bachillerato grado va en blanco o se obtiene del titulo
        grado = ""

    area = _normalizar_area(candidatos_area[0]) if candidatos_area else ""
    if not area:
        area = _normalizar_area(filename)

    titulo = os.path.splitext(filename)[0].strip()
    safe_filename = get_valid_filename(filename)

    grado_slug = _slug(grado) if nivel != "bachillerato" else "_"
    s3_key = f"documentos/2026/{nivel or '_'}/{grado_slug}/{periodo or '_'}/{_slug(area)}/{safe_filename}"
    s3_key = _cap_key(s3_key)

    local_path = LOCAL_DIR_BASE / path

    return {
        "id": item["id"],
        "filename": filename,
        "titulo": titulo,
        "nivel": nivel,
        "grado": grado,
        "periodo": periodo,
        "area": area,
        "s3_key": s3_key,
        "local_path": local_path,
        "rel_path": path,
    }


def obtener_s3_client():
    return boto3.client(
        "s3",
        endpoint_url=R2_ENDPOINT,
        aws_access_key_id=R2_ACCESS_KEY,
        aws_secret_access_key=R2_SECRET_KEY,
        region_name="auto",
    )


def listar_keys_r2(s3):
    print("Consultando llaves existentes en Cloudflare R2 (documentos/2026/)...")
    keys = set()
    continuation_token = None
    while True:
        kwargs = {"Bucket": R2_BUCKET, "Prefix": "documentos/2026/"}
        if continuation_token:
            kwargs["ContinuationToken"] = continuation_token
        res = s3.list_objects_v2(**kwargs)
        for obj in res.get("Contents", []):
            keys.add(obj["Key"])
        if res.get("IsTruncated"):
            continuation_token = res.get("NextContinuationToken")
        else:
            break
    print(f"Total llaves encontradas en R2 bajo documentos/2026/: {len(keys)}")
    return keys


def descargar_archivo(item):
    local_path = item["local_path"]
    if local_path.exists() and local_path.stat().st_size > 1000:
        return True, "ya descargado"

    local_path.parent.mkdir(parents=True, exist_ok=True)
    temp_target = str(local_path) + ".tmp"
    retries = 3
    for attempt in range(retries):
        try:
            res = gdown.download(id=item["id"], output=temp_target, quiet=True)
            if res and os.path.exists(temp_target) and os.path.getsize(temp_target) > 500:
                os.replace(temp_target, local_path)
                return True, "descargado ok"
        except Exception as e:
            if attempt == retries - 1:
                if os.path.exists(temp_target):
                    try:
                        os.remove(temp_target)
                    except Exception:
                        pass
                return False, f"error descarga: {e}"
            time.sleep(1.5 * (attempt + 1))
    return False, "falla tras reintentos"


def subir_archivo_r2(s3, item, r2_keys):
    s3_key = item["s3_key"]
    if s3_key in r2_keys:
        return True, "ya en R2"

    local_path = item["local_path"]
    if not local_path.exists():
        return False, "archivo local no existe"

    try:
        s3.upload_file(
            str(local_path),
            R2_BUCKET,
            s3_key,
            ExtraArgs={"ContentType": "application/pdf"},
        )
        r2_keys.add(s3_key)
        return True, "subido a R2"
    except Exception as e:
        return False, f"error subida R2: {e}"


def procesar_guia(item, s3, r2_keys):
    # 1. Descargar si hace falta
    ok_dl, msg_dl = descargar_archivo(item)
    if not ok_dl:
        return False, f"Descarga fallida: {item['filename']} -> {msg_dl}"

    # 2. Subir a R2 si hace falta
    ok_r2, msg_r2 = subir_archivo_r2(s3, item, r2_keys)
    if not ok_r2:
        return False, f"R2 fallido: {item['filename']} -> {msg_r2}"

    return True, "ok"


def registrar_en_bd(items_parsed):
    print("\nSincronizando secuencia de IDs en PostgreSQL...")
    with connections["default"].cursor() as cursor:
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('"DOCUMENTOS"', 'id'), coalesce(max(id), 1) + 1, false) FROM "DOCUMENTOS";
        """)
    print("Registrando documentos en base de datos PostgreSQL (Supabase)...")
    creados = 0
    actualizados = 0

    for it in items_parsed:
        doc, created = Documento.objects.update_or_create(
            categoria="guia",
            anio=2026,
            titulo=it["titulo"],
            defaults={
                "nivel": it["nivel"],
                "grado": it["grado"],
                "periodo": it["periodo"],
                "area": it["area"],
                "archivo": it["s3_key"],
            },
        )
        if created:
            creados += 1
        else:
            actualizados += 1

    total_2026 = Documento.objects.filter(categoria="guia", anio=2026).count()
    total_general = Documento.objects.count()
    print(f"BD Supabase: {creados} nuevos, {actualizados} actualizados.")
    print(f"Total guias 2026 en Supabase: {total_2026}")
    print(f"Total documentos general en Supabase: {total_general}")


def sincronizar_a_sqlite(items_parsed):
    print("\nSincronizando registros a base de datos SQLite local (db.sqlite3)...")
    import sqlite3
    sqlite_path = BASE_DIR / "db.sqlite3"
    if not sqlite_path.exists():
        print("db.sqlite3 no existe localmente, omitiendo.")
        return

    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    creados = 0
    actualizados = 0
    from datetime import date
    hoy = date.today().isoformat()

    for it in items_parsed:
        cursor.execute(
            "SELECT id FROM DOCUMENTOS WHERE categoria='guia' AND anio=2026 AND titulo=?",
            (it["titulo"],),
        )
        row = cursor.fetchone()
        if row:
            doc_id = row[0]
            cursor.execute(
                """
                UPDATE DOCUMENTOS
                SET nivel=?, grado=?, periodo=?, area=?, RUTA_ARCHIVO=?
                WHERE id=?
                """,
                (it["nivel"], it["grado"], it["periodo"], it["area"], it["s3_key"], doc_id),
            )
            actualizados += 1
        else:
            cursor.execute(
                """
                INSERT INTO DOCUMENTOS
                (titulo, RUTA_ARCHIVO, categoria, anio, nivel, grado, periodo, area, descripcion, orden, fecha)
                VALUES (?, ?, 'guia', 2026, ?, ?, ?, ?, '', 0, ?)
                """,
                (it["titulo"], it["s3_key"], it["nivel"], it["grado"], it["periodo"], it["area"], hoy),
            )
            creados += 1

    conn.commit()
    cursor.execute("SELECT count(*) FROM DOCUMENTOS WHERE categoria='guia' AND anio=2026")
    total_2026 = cursor.fetchone()[0]
    cursor.execute("SELECT count(*) FROM DOCUMENTOS")
    total_gen = cursor.fetchone()[0]
    conn.close()
    print(f"SQLite local: {creados} nuevos, {actualizados} actualizados.")
    print(f"Total guias 2026 en SQLite: {total_2026}")
    print(f"Total documentos general en SQLite: {total_gen}")


def main():
    if not CACHE_FILE.exists():
        print(f"Error: no existe {CACHE_FILE}")
        sys.exit(1)

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        raw_items = json.load(f)

    print(f"Iniciando migracion de {len(raw_items)} guias de 2026...")
    items_parsed = [parse_metadata(it) for it in raw_items]

    s3 = obtener_s3_client()
    r2_keys = listar_keys_r2(s3)

    # Identificar que falta descargar o subir
    faltan_proceso = []
    for it in items_parsed:
        necesita_dl = not (it["local_path"].exists() and it["local_path"].stat().st_size > 1000)
        necesita_r2 = it["s3_key"] not in r2_keys
        if necesita_dl or necesita_r2:
            faltan_proceso.append(it)

    print(f"Archivos listos completos: {len(items_parsed) - len(faltan_proceso)}")
    print(f"Archivos pendientes de descarga/subida: {len(faltan_proceso)}")

    if faltan_proceso:
        print(f"\nDescargando y subiendo {len(faltan_proceso)} archivos con 6 hilos concurrentes...")
        completados = 0
        fallos = 0

        with ThreadPoolExecutor(max_workers=6) as executor:
            future_to_item = {
                executor.submit(procesar_guia, it, s3, r2_keys): it for it in faltan_proceso
            }
            for future in as_completed(future_to_item):
                it = future_to_item[future]
                try:
                    ok, msg = future.result()
                    if ok:
                        completados += 1
                    else:
                        fallos += 1
                        print(f"  Fallo: {msg}")
                except Exception as exc:
                    fallos += 1
                    print(f"  Excepcion con {it['filename']}: {exc}")

                tot = completados + fallos
                if tot % 25 == 0 or tot == len(faltan_proceso):
                    print(f"  Progreso: {tot}/{len(faltan_proceso)} procesados ({completados} exitosos, {fallos} fallos)")

        print(f"\nFase de archivos terminada: {completados} procesados exitosamente, {fallos} fallos.")

    # Registrar en Supabase
    registrar_en_bd(items_parsed)

    # Registrar en SQLite
    sincronizar_a_sqlite(items_parsed)

    print("\nMigracion de guias 2026 finalizada con exito.")


if __name__ == "__main__":
    main()
