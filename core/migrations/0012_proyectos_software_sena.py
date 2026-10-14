from django.db import migrations

GRUPO_INCLUSION = "Software de Inclusión"
GRUPO_GESTION = "Software de Gestión Escolar"

PROYECTOS = [
    {
        "clave": "bdei", "orden": 10, "grupo": GRUPO_INCLUSION,
        "titulo": "B.A.D.E.I · Boletín Digital Académico de Inclusión",
        "enlace": "https://bdei-one.vercel.app",
        "contenido": (
            "B.A.D.E.I es la plataforma que genera los boletines descriptivos de los estudiantes de inclusión educativa del colegio, "
            "en línea con el Decreto 1421 de 2017.\n\n"
            "Qué permite hacer: gestionar el perfil de cada estudiante, registrar su PIAR (Plan Individual de Ajustes Razonables), "
            "llevar el registro académico por periodo y generar boletines descriptivos listos para exportar.\n\n"
            "Para quién: docentes de apoyo y docentes de aula. El acceso es con usuario y contraseña porque maneja información "
            "sensible de los estudiantes."
        ),
    },
    {
        "clave": "eco-inclusivo", "orden": 20, "grupo": GRUPO_INCLUSION,
        "titulo": "Eco Inclusivo · Plataforma de Educación Inclusiva",
        "enlace": "https://plataforma-inclusion-adaptativa.vercel.app",
        "contenido": (
            "Eco Inclusivo es una plataforma de aprendizaje para estudiantes con discapacidad intelectual. Cada guía PIAR se convierte "
            "en una ruta: un camino de pasos ordenados que el estudiante recorre uno a uno, con actividades diseñadas para su ritmo.\n\n"
            "Qué permite hacer: el docente crea actividades en un banco de plantillas, las convierte en rutas por estudiante y "
            "sigue su progreso paso a paso. El estudiante ve solo la actividad que le corresponde, sin distracciones.\n\n"
            "Para quién: docentes de apoyo y estudiantes de inclusión."
        ),
    },
    {
        "clave": "edupass", "orden": 10, "grupo": GRUPO_GESTION,
        "titulo": "EduPass · Sistema de Asistencia C.E.I.S",
        "enlace": "https://senaedupassceis.netlify.app",
        "contenido": (
            "EduPass controla la asistencia y los ingresos al colegio con carné QR.\n\n"
            "Tres módulos: Punto de Acceso, para que portería escanee el carné y registre entradas, retardos, faltas de uniforme o "
            "evasiones; Padres de Familia, para consultar las novedades de su estudiante con su documento; y Administrador, "
            "para cargar la lista de estudiantes desde Excel.\n\n"
            "Para quién: portería, directivos y familias."
        ),
    },
    {
        "clave": "atdie", "orden": 20, "grupo": GRUPO_GESTION,
        "titulo": "ATDIE · Sistema de Inventario Escolar",
        "enlace": "https://frontend-kohl-mu-2yl7qw0tj0.vercel.app",
        "contenido": (
            "ATDIE es el sistema de inventario de los recursos didácticos y de laboratorio del colegio, organizado por áreas: "
            "Matemáticas, Biología, Física, Química, Educación Física y Español.\n\n"
            "Qué permite hacer: registrar y consultar el material de cada área, saber qué hay disponible y mantener el inventario "
            "al día con usuarios de administrador y de profesor.\n\n"
            "Para quién: docentes y administración."
        ),
    },
]


def crear(apps, schema_editor):
    Seccion = apps.get_model("core", "Seccion")
    for p in PROYECTOS:
        # get_or_create: no pisa lo que el rector ya haya editado.
        Seccion.objects.get_or_create(
            clave=p["clave"],
            defaults={
                "titulo": p["titulo"], "contenido": p["contenido"],
                "categoria": "proyecto", "orden": p["orden"],
                "grupo": p["grupo"], "enlace_externo": p["enlace"],
            },
        )


def borrar(apps, schema_editor):
    apps.get_model("core", "Seccion").objects.filter(
        clave__in=[p["clave"] for p in PROYECTOS]).delete()


class Migration(migrations.Migration):
    dependencies = [("core", "0011_seccion_enlace_grupo")]
    operations = [migrations.RunPython(crear, borrar)]
