import os
import re
import unicodedata
from django.utils.text import get_valid_filename

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


def sin_acentos(s: str) -> str:
    if not s:
        return ""
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def slug(s: str) -> str:
    s = re.sub(r"[^\w\-]+", "-", sin_acentos(s)).strip("-").lower()
    return s or "_"


def cap_key(key: str, limite: int = 240) -> str:
    if len(key) <= limite:
        return key
    carpeta, _, nombre = key.rpartition("/")
    stem, ext = os.path.splitext(nombre)
    stem = stem[:max(8, len(stem) - (len(key) - limite))]
    return f"{carpeta}/{stem}{ext}"


def normalizar_area(texto: str) -> str:
    t = sin_acentos(texto).lower()
    for clave, valor in _REGLAS_AREA:
        if clave in t:
            return valor
    return texto.strip().title() if texto else "General"


def parsear_nombre_guia(filename: str, default_anio: int = 2026, default_periodo: str = "") -> dict:
    """Analiza de forma heurística el nombre de un archivo de guía y extrae
    automáticamente: año, período, nivel, grado, área y título limpio."""
    stem = os.path.splitext(filename)[0].strip()
    u = sin_acentos(stem).upper()

    # 1. Año
    m_anio = re.search(r"\b(202[0-9])\b", u)
    anio = int(m_anio.group(1)) if m_anio else default_anio

    # 2. Período
    periodo = default_periodo or ""
    if not periodo:
        m_per = re.search(r"\b(IV|III|II|I)\s*(?:PERIODO|PERÍODO|PER)?\b", u)
        if m_per and m_per.group(1) in ("IV", "III", "II", "I"):
            periodo = m_per.group(1)
        else:
            m_g = re.search(r"\bGU[IÍ]A\s*([1-4])\b", u)
            if m_g:
                romanos = {"1": "I", "2": "II", "3": "III", "4": "IV"}
                periodo = romanos.get(m_g.group(1), "I")
            else:
                m_p = re.search(r"\bP([1-4])\b", u)
                if m_p:
                    romanos = {"1": "I", "2": "II", "3": "III", "4": "IV"}
                    periodo = romanos.get(m_p.group(1), "I")
                else:
                    periodo = "I"

    # 3. Nivel y Grado
    nivel = ""
    grado = ""

    if re.search(r"(transici|jard|prejard|infantil)", u, re.I):
        nivel = "preescolar"
        if "PREJARD" in u:
            grado = "Prejardín"
        elif "JARD" in u:
            grado = "Jardín"
        else:
            grado = "Transición"
    else:
        # Bachillerato explicito (6° a 11°)
        m_bach = re.search(r"\b(1[0-1]|[6-9])\s*[°º]", u) or re.search(r"\bGRADO\s*(1[0-1]|[6-9])\b", u)
        # Primaria explicito (1° a 5°)
        m_prim = re.search(r"\b([1-5])\s*[°º]", u) or re.search(r"\bGRADO\s*([1-5])\b", u)

        if m_bach:
            nivel = "bachillerato"
            grado = f"{m_bach.group(1)}°"
        elif m_prim:
            nivel = "primaria"
            grado = f"{m_prim.group(1)}º"
        elif "PRIMARIA" in u:
            nivel = "primaria"
            m = re.search(r"\b([1-5])\b", u)
            grado = f"{m.group(1)}º" if m else ""
        elif "BACHILLER" in u:
            nivel = "bachillerato"
            m = re.search(r"\b(1[0-1]|[6-9])\b", u)
            grado = f"{m.group(1)}°" if m else ""
        else:
            # Deteccion de 10 u 11 sin simbolo
            m_media = re.search(r"\b(1[0-1])\b", u)
            if m_media:
                nivel = "bachillerato"
                grado = f"{m_media.group(1)}°"
            else:
                nivel = "bachillerato"
                grado = ""

    # 4. Área
    area = normalizar_area(stem)

    # 5. Clave de almacenamiento jerárquica
    safe_filename = get_valid_filename(filename)
    grado_slug = slug(grado) if nivel != "bachillerato" else "_"
    s3_key = f"documentos/{anio}/{nivel or '_'}/{grado_slug}/{periodo or '_'}/{slug(area)}/{safe_filename}"
    s3_key = cap_key(s3_key)

    return {
        "filename": filename,
        "titulo": stem,
        "anio": anio,
        "periodo": periodo,
        "nivel": nivel,
        "grado": grado,
        "area": area,
        "s3_key": s3_key,
    }
