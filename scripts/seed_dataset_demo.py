import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import django
import random
import openpyxl

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import DatasetAnalisis
from core.dataset_parser import procesar_archivo_dataset, generar_diagnostico_dataset_ia
from django.core.files import File

def generar_dataset_demo():
    filepath = "media/datasets/icfes_saber11_ceis_historico_2022_2025.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Resultados Saber 11"

    headers = [
        "Año",
        "Documento",
        "Puntaje Global",
        "Lectura Crítica",
        "Matemáticas",
        "Sociales y Ciudadanas",
        "Ciencias Naturales",
        "Inglés"
    ]
    ws.append(headers)

    # Parametros por cohorte para reflejar progreso positivo
    cohortes = {
        2022: {"count": 48, "global_base": 268, "mat": 52, "lec": 54, "soc": 53, "cie": 51, "ing": 50},
        2023: {"count": 52, "global_base": 278, "mat": 55, "lec": 57, "soc": 54, "cie": 53, "ing": 52},
        2024: {"count": 55, "global_base": 289, "mat": 58, "lec": 59, "soc": 57, "cie": 56, "ing": 55},
        2025: {"count": 60, "global_base": 305, "mat": 63, "lec": 64, "soc": 61, "cie": 60, "ing": 59},
    }

    random.seed(42)
    doc_seq = 10123000

    for anio, cfg in cohortes.items():
        for _ in range(cfg["count"]):
            doc_seq += random.randint(1, 5)
            # Simular puntajes con distribucion realista
            mat = max(20, min(100, int(random.gauss(cfg["mat"], 6))))
            lec = max(20, min(100, int(random.gauss(cfg["lec"], 5))))
            soc = max(20, min(100, int(random.gauss(cfg["soc"], 6))))
            cie = max(20, min(100, int(random.gauss(cfg["cie"], 6))))
            ing = max(20, min(100, int(random.gauss(cfg["ing"], 7))))
            pg = int(round((mat * 3 + lec * 3 + soc * 3 + cie * 3 + ing * 1) / 13 * 5))

            ws.append([
                anio,
                str(doc_seq),
                pg,
                lec,
                mat,
                soc,
                cie,
                ing
            ])

    wb.save(filepath)
    print(f"Archivo Excel generado exitosamente en {filepath}")

    # Procesar archivo con el parser
    with open(filepath, "rb") as f:
        datos_norm = procesar_archivo_dataset(f, "icfes_saber11_ceis_historico_2022_2025.xlsx")

    # Guardar en base de datos
    ds, created = DatasetAnalisis.objects.get_or_create(
        titulo="Resultados Históricos Pruebas ICFES Saber 11° (2022 - 2025)",
        defaults={
            "categoria": "icfes",
            "descripcion": "Consolidado de pruebas Saber 11° del I.E.D. Complejo Educativo Integral Sopó (CEIS) comparando cohortes 2022 a 2025 para análisis de evolución y competencias.",
            "datos_normalizados": datos_norm,
        }
    )

    with open(filepath, "rb") as f:
        ds.archivo.save("icfes_saber11_ceis_historico_2022_2025.xlsx", File(f), save=True)

    ds.datos_normalizados = datos_norm
    # Generar diagnóstico con Qwen 3.8 27B
    print("Invocando Athena IA (Qwen 3.8 27B) para diagnóstico...")
    diag = generar_diagnostico_dataset_ia(ds)
    ds.diagnostico_ia = diag
    ds.save()

    print(f"Dataset id={ds.id} '{ds.titulo}' guardado con diagnóstico de longitud {len(diag)} caracteres.")

if __name__ == "__main__":
    generar_dataset_demo()
