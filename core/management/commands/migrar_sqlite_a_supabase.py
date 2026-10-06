import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.contrib.auth.models import User
from core.models import Anio, Periodo, Curso, Materia, Guia, Noticia, Video, Seccion, Imagen, Documento

class Command(BaseCommand):
    help = "Migra todos los datos de db.sqlite3 local a Supabase PostgreSQL usando bulk_create"

    def handle(self, *args, **options):
        sqlite_path = Path(__file__).resolve().parent.parent.parent.parent / "db.sqlite3"
        if not sqlite_path.exists():
            self.stderr.write(self.style.ERROR(f"No se encontró {sqlite_path}"))
            return

        self.stdout.write(self.style.SUCCESS(f"Leyendo datos desde {sqlite_path}..."))
        sqlite_conn = sqlite3.connect(sqlite_path)
        sqlite_conn.row_factory = sqlite3.Row

        with transaction.atomic():
            # 1. Usuarios (Auth)
            cursor = sqlite_conn.cursor()
            cursor.execute("SELECT * FROM auth_user")
            objs = [
                User(
                    id=u['id'],
                    password=u['password'],
                    last_login=u['last_login'],
                    is_superuser=bool(u['is_superuser']),
                    username=u['username'],
                    first_name=u['first_name'],
                    last_name=u['last_name'],
                    email=u['email'],
                    is_staff=bool(u['is_staff']),
                    is_active=bool(u['is_active']),
                    date_joined=u['date_joined'],
                ) for u in cursor.fetchall()
            ]
            User.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Usuarios: {len(objs)} migrados"))

            # 2. Años
            cursor.execute("SELECT * FROM ANIOS")
            objs = [Anio(id=a['id'], anio=a['anio'], activo=bool(a['activo'])) for a in cursor.fetchall()]
            Anio.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Años (ANIOS): {len(objs)} migrados"))

            # 3. Períodos
            cursor.execute("SELECT * FROM PERIODOS")
            objs = [Periodo(id=p['id'], anio_id=p['anio_id'], numero=p['numero'], nombre=p['nombre'] or '') for p in cursor.fetchall()]
            Periodo.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Períodos (PERIODOS): {len(objs)} migrados"))

            # 4. Cursos
            cursor.execute("SELECT * FROM CURSOS")
            objs = [Curso(id=c['id'], periodo_id=c['periodo_id'], nombre=c['nombre'], nivel=c['nivel'] or '') for c in cursor.fetchall()]
            Curso.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Cursos (CURSOS): {len(objs)} migrados"))

            # 5. Materias
            cursor.execute("SELECT * FROM MATERIAS")
            objs = [Materia(id=m['id'], curso_id=m['curso_id'], nombre=m['nombre']) for m in cursor.fetchall()]
            Materia.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Materias (MATERIAS): {len(objs)} migrados"))

            # 6. Guías
            cursor.execute("SELECT * FROM GUIAS")
            objs = [
                Guia(
                    id=g['id'],
                    materia_id=g['materia_id'],
                    titulo=g['titulo'],
                    descripcion=g['descripcion'] or '',
                    archivo=g['RUTA_ARCHIVO'],
                    fecha_publicacion=g['fecha_publicacion'],
                ) for g in cursor.fetchall()
            ]
            Guia.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Guías (GUIAS): {len(objs)} migradas"))

            # 7. Noticias
            cursor.execute("SELECT * FROM NOTICIAS")
            objs = [
                Noticia(
                    id=n['id'],
                    titulo=n['titulo'],
                    cuerpo=n['cuerpo'],
                    fecha_publicacion=n['fecha_publicacion'],
                    activo=bool(n['activo']),
                ) for n in cursor.fetchall()
            ]
            Noticia.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Noticias (NOTICIAS): {len(objs)} migradas"))

            # 8. Videos
            cursor.execute("SELECT * FROM VIDEOS")
            objs = [
                Video(
                    id=v['id'],
                    titulo=v['titulo'],
                    youtube_url=v['youtube_url'],
                    descripcion=v['descripcion'] or '',
                    fecha=v['fecha'],
                ) for v in cursor.fetchall()
            ]
            Video.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Videos (VIDEOS): {len(objs)} migrados"))

            # 9. Secciones
            cursor.execute("SELECT * FROM SECCIONES")
            objs = [
                Seccion(
                    id=s['id'],
                    clave=s['clave'],
                    titulo=s['titulo'],
                    contenido=s['contenido'] or '',
                    categoria=s['categoria'],
                    orden=s['orden'],
                ) for s in cursor.fetchall()
            ]
            Seccion.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Secciones (SECCIONES): {len(objs)} migradas"))

            # 10. Imágenes
            cursor.execute("SELECT * FROM IMAGENES")
            objs = [
                Imagen(
                    id=img['id'],
                    seccion_id=img['seccion_id'],
                    titulo=img['titulo'] or '',
                    archivo=img['RUTA_ARCHIVO'],
                    orden=img['orden'],
                    fecha=img['fecha'],
                ) for img in cursor.fetchall()
            ]
            Imagen.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Imágenes (IMAGENES): {len(objs)} migradas"))

            # 11. Documentos
            cursor.execute("SELECT * FROM DOCUMENTOS")
            objs = [
                Documento(
                    id=doc['id'],
                    titulo=doc['titulo'],
                    archivo=doc['RUTA_ARCHIVO'],
                    categoria=doc['categoria'],
                    anio=doc['anio'],
                    nivel=doc['nivel'] or '',
                    grado=doc['grado'] or '',
                    periodo=doc['periodo'] or '',
                    area=doc['area'] or '',
                    descripcion=doc['descripcion'] or '',
                    orden=doc['orden'],
                    fecha=doc['fecha'],
                ) for doc in cursor.fetchall()
            ]
            Documento.objects.bulk_create(objs, ignore_conflicts=True, batch_size=500)
            self.stdout.write(self.style.SUCCESS(f"✓ Documentos (DOCUMENTOS): {len(objs)} migrados"))

        # Actualizar las secuencias de Postgres para autoincremento correcto
        with connection.cursor() as pg_cursor:
            tables = [
                ("auth_user", "auth_user_id_seq"),
                ("ANIOS", "ANIOS_id_seq"),
                ("PERIODOS", "PERIODOS_id_seq"),
                ("CURSOS", "CURSOS_id_seq"),
                ("MATERIAS", "MATERIAS_id_seq"),
                ("GUIAS", "GUIAS_id_seq"),
                ("NOTICIAS", "NOTICIAS_id_seq"),
                ("VIDEOS", "VIDEOS_id_seq"),
                ("SECCIONES", "SECCIONES_id_seq"),
                ("IMAGENES", "IMAGENES_id_seq"),
                ("DOCUMENTOS", "DOCUMENTOS_id_seq"),
            ]
            for table, seq in tables:
                try:
                    pg_cursor.execute(f"SELECT setval('{seq}', (SELECT COALESCE(MAX(id), 1) FROM \"{table}\"));")
                except Exception:
                    pass

        self.stdout.write(self.style.SUCCESS("\n🎉 MIGRACIÓN COMPLETA Y EXITOSA A SUPABASE POSTGRESQL!"))
