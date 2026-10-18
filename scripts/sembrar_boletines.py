import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from core.models import Estudiante, InformeValorativo

DATOS_QUIROGA = {
    "areas": [
        {
            "nombre": "PENSAMIENTO CIENTÍFICO",
            "asignaturas": [
                {
                    "nombre": "QUÍMICA",
                    "p1": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 8, "total": 71, "des": "BS"},
                    "p3": {"p": 7, "rd": 17, "r": 27, "a": 28, "pt": 8, "total": 87, "des": "A"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                },
                {
                    "nombre": "FÍSICA",
                    "p1": {"p": 8, "rd": 18, "r": 28, "a": 27, "pt": 9, "total": 90, "des": "S"},
                    "p2": {"p": 10, "rd": 18, "r": 21, "a": 21, "pt": 7, "total": 77, "des": "BS"},
                    "p3": {"p": 10, "rd": 18, "r": 25, "a": 25, "pt": 9, "total": 87, "des": "A"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                },
                {
                    "nombre": "BIOLOGÍA",
                    "p1": {"p": 7, "rd": 14, "r": 28, "a": 23, "pt": 8, "total": 80, "des": "A"},
                    "p2": {"p": 10, "rd": 14, "r": 24, "a": 22, "pt": 9, "total": 79, "des": "BS"},
                    "p3": {"p": 10, "rd": 17, "r": 27, "a": 21, "pt": 8, "total": 83, "des": "A"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 10, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO MATEMÁTICO",
            "asignaturas": [
                {
                    "nombre": "MATEMÁTICAS",
                    "p1": {"p": 10, "rd": 16, "r": 21, "a": 21, "pt": 8, "total": 76, "des": "BS"},
                    "p2": {"p": 10, "rd": 18, "r": 26, "a": 24, "pt": 7, "total": 85, "des": "A"},
                    "p3": {"p": 10, "rd": 20, "r": 30, "a": 24, "pt": 10, "total": 94, "des": "S"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        },
        {
            "nombre": "COMUNICACIONES (HUMANIDADES)",
            "asignaturas": [
                {
                    "nombre": "LENGUA CASTELLANA",
                    "p1": {"p": 9, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 72, "des": "BS"},
                    "p2": {"p": 10, "rd": 20, "r": 30, "a": 30, "pt": 7, "total": 97, "des": "S"},
                    "p3": {"p": 7, "rd": 18, "r": 30, "a": 30, "pt": 9, "total": 94, "des": "S"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                },
                {
                    "nombre": "INGLÉS",
                    "p1": {"p": 10, "rd": 20, "r": 21, "a": 25, "pt": 10, "total": 86, "des": "A"},
                    "p2": {"p": 10, "rd": 15, "r": 21, "a": 21, "pt": 10, "total": 77, "des": "BS"},
                    "p3": {"p": 10, "rd": 20, "r": 24, "a": 24, "pt": 10, "total": 88, "des": "A"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO SOCIAL",
            "asignaturas": [
                {
                    "nombre": "P. POLITICO Y ECONOMICO",
                    "p1": {"p": 8, "rd": 18, "r": 27, "a": 25, "pt": 8, "total": 86, "des": "A"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p3": {"p": 7, "rd": 16, "r": 25, "a": 24, "pt": 9, "total": 81, "des": "BJ"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                },
                {
                    "nombre": "PENSAMIENTO SOCIAL",
                    "p1": {"p": 8, "rd": 14, "r": 24, "a": 21, "pt": 7, "total": 74, "des": "BS"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p3": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 8, "total": 71, "des": "BS"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 9, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO FILOSOFICO",
            "asignaturas": [
                {
                    "nombre": "FILOSOFIA",
                    "p1": {"p": 8, "rd": 18, "r": 24, "a": 24, "pt": 9, "total": 83, "des": "A"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p3": {"p": 8, "rd": 19, "r": 27, "a": 26, "pt": 10, "total": 90, "des": "S"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        },
        {
            "nombre": "CULTURA FÍSICA Y DEPORTIVA",
            "asignaturas": [
                {
                    "nombre": "EDUCACIÓN FÍSICA",
                    "p1": {"p": 10, "rd": 20, "r": 30, "a": 30, "pt": 10, "total": 100, "des": "S"},
                    "p2": {"p": 10, "rd": 20, "r": 30, "a": 30, "pt": 10, "total": 100, "des": "S"},
                    "p3": {"p": 8, "rd": 18, "r": 21, "a": 22, "pt": 8, "total": 77, "des": "BS"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO ARTÍSTICO",
            "asignaturas": [
                {
                    "nombre": "EDUCACIÓN ARTÍSTICA",
                    "p1": {"p": 8, "rd": 14, "r": 21, "a": 21, "pt": 8, "total": 72, "des": "BS"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 23, "pt": 10, "total": 75, "des": "BS"},
                    "p3": {"p": 7, "rd": 16, "r": 26, "a": 23, "pt": 10, "total": 82, "des": "A"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO ÉTICO Y CIUDADANO",
            "asignaturas": [
                {
                    "nombre": "EDUCACIÓN ÉTICA Y RELIGIOSA",
                    "p1": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p3": {"p": 7, "rd": 15, "r": 21, "a": 24, "pt": 8, "total": 75, "des": "BS"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 7, "des": "-"}
                }
            ]
        },
        {
            "nombre": "PENSAMIENTO TECNOLÓGICO",
            "asignaturas": [
                {
                    "nombre": "TECNOLOGÍA E INFORMÁTICA",
                    "p1": {"p": 8, "rd": 14, "r": 21, "a": 21, "pt": 8, "total": 72, "des": "BS"},
                    "p2": {"p": 7, "rd": 14, "r": 21, "a": 21, "pt": 7, "total": 70, "des": "BS"},
                    "p3": {"p": 7, "rd": 14, "r": 24, "a": 21, "pt": 7, "total": 73, "des": "BS"},
                    "p4": {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
                }
            ]
        }
    ],
    "promedio_actitudinal": {"p1": "8,15", "p2": "7,92", "p3": "8,76", "p4": "0,00"},
    "tecnico_sena": {"p1": "A", "p2": "BS", "p3": "A", "p4": "-"}
}

CONVIVENCIA_QUIROGA = {
    "convivencia": {
        "p1": {"pa": "8,2", "vc": "8", "pc": "80,8", "des": "A"},
        "p2": {"pa": "7,9", "vc": "7", "pc": "74,6", "des": "BS"},
        "p3": {"pa": "8,8", "vc": "10", "pc": "93,8", "des": "S"},
        "p4": {"pa": "0,0", "vc": "-", "pc": "0,0", "des": "-"}
    },
    "ambito_familiar": {"p1": "S", "p2": "S", "p3": "S", "p4": "-"},
    "fallas_retardos": {
        "p1": {"f": 0, "r": 5, "e": 0, "u": 0},
        "p2": {"f": 7, "r": 4, "e": 0, "u": 4},
        "p3": {"f": 0, "r": 1, "e": 0, "u": 0},
        "p4": {"f": 0, "r": 3, "e": 0, "u": 0}
    }
}

def sembrar():
    # 1. Sembrar el estudiante oficial del documento
    estudiante, _ = Estudiante.objects.update_or_create(
        documento="1075876349",
        defaults={
            "tipo_documento": "Tarjeta de Identidad",
            "nombres": "JUAN SEBASTIAN",
            "apellidos": "QUIROGA GONZALEZ",
            "grado": "UNDECIMO",
            "curso": "1101",
            "director_grupo": "ROJAS GUTIERREZ LILIANA ASTRID",
            "acudiente": "MARIA GONZALEZ",
            "activo": True,
        }
    )

    informe, _ = InformeValorativo.objects.update_or_create(
        estudiante=estudiante,
        anio_lectivo=2026,
        defaults={
            "periodo_actual": 3,
            "datos_academicos": DATOS_QUIROGA,
            "datos_convivencia": CONVIVENCIA_QUIROGA,
            "observaciones_academicas": (
                "Firma compromiso académico\n\n"
                "El estudiante debe presentar el desarrollo completo de las guías no alcanzadas en el menor tiempo posible.\n"
                "A la fecha, el aprendiz SENA ha cumplido con la entrega de las evidencias propuestas."
            ),
            "observaciones_convivenciales": (
                "La institución agradece su colaboración en las campañas de mejora .\n\n"
                "Felicitaciones por su aporte a la convivencia institucional."
            ),
            "tecnico_sena": "A"
        }
    )
    print(f"Estudiante sembrado: {estudiante.nombre_completo} (Doc: {estudiante.documento})")

    # 2. Sembrar también un estudiante de 6° de prueba
    est_sexto, _ = Estudiante.objects.update_or_create(
        documento="1076745451",
        defaults={
            "tipo_documento": "Tarjeta de Identidad",
            "nombres": "ITAN ANDREY",
            "apellidos": "ALARCON MARTINEZ",
            "grado": "SEXTO",
            "curso": "601",
            "director_grupo": "CARDENAS FORERO MARTHA",
            "acudiente": "Andrea Martinez Ortiz",
            "activo": True,
        }
    )
    InformeValorativo.objects.update_or_create(
        estudiante=est_sexto,
        anio_lectivo=2026,
        defaults={
            "periodo_actual": 3,
            "datos_academicos": DATOS_QUIROGA,  # Plantilla académica coherente
            "datos_convivencia": CONVIVENCIA_QUIROGA,
            "observaciones_academicas": "Felicitaciones por el avance en las guías del Sistema Educativo Relacional.",
            "observaciones_convivenciales": "Excelente participación y compromiso con el manual de convivencia.",
            "tecnico_sena": "A"
        }
    )
    print(f"Estudiante 601 sembrado: {est_sexto.nombre_completo} (Doc: {est_sexto.documento})")

if __name__ == "__main__":
    sembrar()
