"""
Modelos de Athena — las entidades del esquema.

Jerarquía de las guías (lo más importante):

    AÑO → PERÍODO (1–4) → CURSO → MATERIA → GUÍAS

Regla de arquitectura: la base de datos guarda SOLO datos estructurados y la
RUTA de cada archivo (FileField -> columna RUTA_ARCHIVO). El archivo pesado
vive en el almacenamiento (media/ en local, Object Storage en producción).

Los nombres de tabla (Meta.db_table) van en MAYÚSCULAS para coincidir con el
esquema Oracle de base-de-datos/esquema_oracle.sql.

USUARIOS (login del rector) NO se define aquí: lo gestiona el sistema de
autenticación de Django (django.contrib.auth). El rector es un superusuario.
"""
import re

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .validators import validar_imagen, validar_pdf


# ===========================================================================
#  Jerarquía de guías
# ===========================================================================
class Anio(models.Model):
    """Año académico. Raíz de la jerarquía."""
    anio = models.PositiveIntegerField("Año", unique=True, help_text="Ej.: 2026")
    activo = models.BooleanField("Activo", default=True,
                                 help_text="Solo los años activos se muestran en la web pública.")

    class Meta:
        db_table = "ANIOS"
        verbose_name = "Año académico"
        verbose_name_plural = "Años académicos"
        ordering = ["-anio"]

    def __str__(self):
        return str(self.anio)


class Periodo(models.Model):
    """Período (1 a 4) de un año."""
    anio = models.ForeignKey(Anio, on_delete=models.CASCADE, related_name="periodos",
                             verbose_name="Año")
    numero = models.PositiveSmallIntegerField(
        "Número", validators=[MinValueValidator(1), MaxValueValidator(4)],
        help_text="Del 1 al 4.")
    nombre = models.CharField("Nombre", max_length=60, blank=True,
                              help_text="Opcional. Ej.: 'Primer período'.")

    class Meta:
        db_table = "PERIODOS"
        verbose_name = "Período"
        verbose_name_plural = "Períodos"
        unique_together = ("anio", "numero")
        ordering = ["anio", "numero"]

    def __str__(self):
        etiqueta = self.nombre or f"Período {self.numero}"
        return f"{self.anio} · {etiqueta}"


class Curso(models.Model):
    """Curso/grupo dentro de un período. Ej.: 6°A, 10°C."""
    periodo = models.ForeignKey(Periodo, on_delete=models.CASCADE, related_name="cursos",
                                verbose_name="Período")
    nombre = models.CharField("Nombre", max_length=40, help_text="Ej.: 6°A")
    nivel = models.CharField("Nivel", max_length=40, blank=True,
                             help_text="Opcional. Ej.: 'Secundaria'.")

    class Meta:
        db_table = "CURSOS"
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    """Materia dentro de un curso. Ej.: Matemáticas."""
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE, related_name="materias",
                              verbose_name="Curso")
    nombre = models.CharField("Nombre", max_length=80)

    class Meta:
        db_table = "MATERIAS"
        verbose_name = "Materia"
        verbose_name_plural = "Materias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Guia(models.Model):
    """Guía de estudio (PDF) de una materia."""
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE, related_name="guias",
                                verbose_name="Materia")
    titulo = models.CharField("Título", max_length=160)
    descripcion = models.TextField("Descripción", blank=True)
    # archivo.name = la RUTA que se guarda en Oracle (columna RUTA_ARCHIVO).
    archivo = models.FileField("Archivo PDF", upload_to="guias/",
                               validators=[validar_pdf], db_column="RUTA_ARCHIVO")
    fecha_publicacion = models.DateField("Fecha de publicación", auto_now_add=True)

    class Meta:
        db_table = "GUIAS"
        verbose_name = "Guía de estudio"
        verbose_name_plural = "Guías de estudio"
        ordering = ["-fecha_publicacion", "titulo"]

    def __str__(self):
        return self.titulo


# ===========================================================================
#  Contenido independiente de la home
# ===========================================================================
class Noticia(models.Model):
    """Anuncio o noticia del colegio."""
    titulo = models.CharField("Título", max_length=160)
    cuerpo = models.TextField("Cuerpo")
    fecha_publicacion = models.DateTimeField("Fecha de publicación", auto_now_add=True)
    activo = models.BooleanField("Activo", default=True,
                                 help_text="Solo las noticias activas aparecen en la web.")

    class Meta:
        db_table = "NOTICIAS"
        verbose_name = "Noticia"
        verbose_name_plural = "Noticias"
        ordering = ["-fecha_publicacion"]

    def __str__(self):
        return self.titulo


class Video(models.Model):
    """Video de YouTube embebido en la web pública."""
    titulo = models.CharField("Título", max_length=160)
    youtube_url = models.URLField("Enlace de YouTube",
                                  help_text="Pega el enlace normal de YouTube; se embebe solo.")
    descripcion = models.TextField("Descripción", blank=True)
    fecha = models.DateField("Fecha", auto_now_add=True)

    class Meta:
        db_table = "VIDEOS"
        verbose_name = "Video"
        verbose_name_plural = "Videos"
        ordering = ["-fecha"]

    def __str__(self):
        return self.titulo

    @property
    def embed_url(self) -> str:
        """Convierte cualquier enlace de YouTube en su URL embebible.
        Soporta watch?v=, youtu.be/, /embed/ y /shorts/."""
        coincidencia = re.search(
            r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", self.youtube_url or "")
        if not coincidencia:
            return ""
        return f"https://www.youtube.com/embed/{coincidencia.group(1)}"


class Seccion(models.Model):
    """Texto editable del sitio: identidad de la home (misión, visión, contacto…)
    y páginas institucionales / proyectos (El Colegio, Proyectos)."""

    class Categoria(models.TextChoices):
        HOME = "home", "Inicio (identidad)"      # no se lista; alimenta la home
        COLEGIO = "colegio", "El Colegio"        # página institucional
        PROYECTO = "proyecto", "Proyectos"       # proyecto transversal

    clave = models.SlugField("Clave", max_length=60, unique=True,
                             help_text="Identificador interno. Ej.: mision, vision, prae.")
    titulo = models.CharField("Título", max_length=160)
    contenido = models.TextField("Contenido", blank=True)
    categoria = models.CharField("Categoría", max_length=20,
                                 choices=Categoria.choices, default=Categoria.HOME)
    orden = models.PositiveIntegerField("Orden", default=0,
                                        help_text="Orden dentro de su categoría.")

    class Meta:
        db_table = "SECCIONES"
        verbose_name = "Sección de texto"
        verbose_name_plural = "Secciones de texto"
        ordering = ["categoria", "orden", "clave"]

    def __str__(self):
        return self.titulo or self.clave


class Imagen(models.Model):
    """Imagen de la galería."""
    titulo = models.CharField("Título", max_length=160, blank=True)
    # archivo.name = la RUTA que se guarda en Oracle (columna RUTA_ARCHIVO).
    archivo = models.FileField("Imagen", upload_to="galeria/",
                               validators=[validar_imagen], db_column="RUTA_ARCHIVO")
    fecha = models.DateField("Fecha", auto_now_add=True)

    class Meta:
        db_table = "IMAGENES"
        verbose_name = "Imagen de galería"
        verbose_name_plural = "Imágenes de galería"
        ordering = ["-fecha"]

    def __str__(self):
        return self.titulo or f"Imagen #{self.pk}"
