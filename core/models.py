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
    archivo = models.FileField("Archivo PDF", upload_to="guias/", max_length=255,
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
    """Imagen de una sección del sitio o de la galería general de la home."""
    seccion = models.ForeignKey("Seccion", null=True, blank=True,
                                on_delete=models.SET_NULL, related_name="imagenes",
                                verbose_name="Sección",
                                help_text="Sección a la que pertenece (vacío = galería general de la home).")
    titulo = models.CharField("Título", max_length=160, blank=True)
    # archivo.name = la RUTA que se guarda en Oracle (columna RUTA_ARCHIVO).
    archivo = models.FileField("Imagen", upload_to="galeria/",
                               validators=[validar_imagen], db_column="RUTA_ARCHIVO")
    orden = models.PositiveIntegerField("Orden", default=0)
    fecha = models.DateField("Fecha", auto_now_add=True)

    class Meta:
        db_table = "IMAGENES"
        verbose_name = "Imagen"
        verbose_name_plural = "Imágenes"
        ordering = ["seccion__orden", "orden", "-fecha"]

    def __str__(self):
        return self.titulo or f"Imagen #{self.pk}"


class Documento(models.Model):
    """Documento institucional (guía SERC, circular, horario, formato, manual…)
    que el rector sube desde el admin y que la web muestra/descarga."""

    class Categoria(models.TextChoices):
        GUIA = "guia", "Guía SERC"
        CIRCULAR = "circular", "Circular"
        CRONOGRAMA = "cronograma", "Cronograma"
        HORARIO = "horario", "Horario"
        FORMATO = "formato", "Formato"
        MANUAL = "manual", "Manual / Institucional"
        OTRO = "otro", "Otro"

    class Nivel(models.TextChoices):
        PREESCOLAR = "preescolar", "Preescolar"
        PRIMARIA = "primaria", "Primaria"
        BACHILLERATO = "bachillerato", "Bachillerato"

    class Periodo(models.TextChoices):
        I = "I", "I Período"
        II = "II", "II Período"
        III = "III", "III Período"
        IV = "IV", "IV Período"

    titulo = models.CharField("Título", max_length=200)
    archivo = models.FileField("Archivo", upload_to="documentos/", max_length=255,
                               db_column="RUTA_ARCHIVO")
    categoria = models.CharField("Categoría", max_length=20,
                                 choices=Categoria.choices, default=Categoria.OTRO)
    anio = models.PositiveIntegerField("Año", null=True, blank=True)
    # Jerarquía de las guías SERC (igual al Drive): Año → Nivel → Grado → Período → Área.
    nivel = models.CharField("Nivel", max_length=12, choices=Nivel.choices, blank=True)
    grado = models.CharField("Grado", max_length=20, blank=True,
                             help_text="Ej.: 9°, 1º, Transición. En bachillerato suele ir en el título.")
    periodo = models.CharField("Período", max_length=3, choices=Periodo.choices, blank=True)
    area = models.CharField("Área / materia", max_length=80, blank=True)
    descripcion = models.TextField("Descripción", blank=True)
    orden = models.PositiveIntegerField("Orden", default=0)
    fecha = models.DateField("Fecha de publicación", auto_now_add=True)

    class Meta:
        db_table = "DOCUMENTOS"
        verbose_name = "Documento"
        verbose_name_plural = "Documentos (circulares, guías…)"
        ordering = ["categoria", "-anio", "nivel", "periodo", "area", "orden", "titulo"]

    def __str__(self):
        return self.titulo

    @property
    def es_pdf(self):
        return (self.archivo.name or "").lower().endswith(".pdf")


class ConfiguracionApariencia(models.Model):
    """Personalización dinámica de colores, tipografía y escala de fuente de la web pública (gestión desde el admin)."""

    class TipografiaPrincipal(models.TextChoices):
        PLUS_JAKARTA = "plus_jakarta_sans", "Plus Jakarta Sans (Moderna y geométrica — Predeterminada)"
        INTER = "inter", "Inter (Neutral y alta legibilidad)"
        OUTFIT = "outfit", "Outfit (Elegante y contemporánea)"
        ROBOTO = "roboto", "Roboto (Clásica y formal)"
        MONTSERRAT = "montserrat", "Montserrat (Institucional y sólida)"
        OPEN_SANS = "open_sans", "Open Sans (Cálida y balanceada)"
        MERRIWEATHER = "merriweather", "Merriweather (Académica tradicional)"

    class TipografiaTitulos(models.TextChoices):
        LORA = "lora", "Lora (Editorial y académica — Predeterminada)"
        PLUS_JAKARTA = "plus_jakarta_sans", "Plus Jakarta Sans (Moderna y limpia)"
        PLAYFAIR = "playfair", "Playfair Display (Clásica refinada)"
        OUTFIT = "outfit", "Outfit (Contemporánea contundente)"
        MONTSERRAT = "montserrat", "Montserrat (Sólida y corporativa)"
        MERRIWEATHER = "merriweather", "Merriweather (Serif formal)"

    class TamanoLetra(models.TextChoices):
        COMPACTO = "compacto", "Compacto (90% — mayor densidad de contenido)"
        NORMAL = "normal", "Estándar (100% — tamaño equilibrado predeterminado)"
        COMODO = "comodo", "Cómodo (+8% — lectura relajada)"
        GRANDE = "grande", "Grande (+16% — alta visibilidad y accesibilidad)"
        MUY_GRANDE = "muy_grande", "Extra Grande (+25% — máxima legibilidad)"

    color_principal = models.CharField("Color Principal (Cabecera/Títulos)", max_length=18, default="#0a1931",
                                       help_text="Color hex para la barra superior, botones y títulos principales. Ej: #0a1931")
    color_secundario = models.CharField("Color Secundario (Menú Principal)", max_length=18, default="#15305b",
                                        help_text="Color hex para la barra del menú principal. Ej: #15305b")
    color_acento = models.CharField("Color de Acento (Bordes/Destacados)", max_length=18, default="#c5a880",
                                    help_text="Color de acento para líneas divisoras y botones destacados. Ej: #c5a880")
    color_acento_suave = models.CharField("Color de Acento Suave", max_length=18, default="#e5d5be",
                                          help_text="Color claro para detalles secundarios. Ej: #e5d5be")
    color_footer = models.CharField("Color del Pie de Página (Footer)", max_length=18, default="#0b6d71",
                                    help_text="Color para el pie de página. Ej: #0b6d71")
    color_texto = models.CharField("Color de Texto Principal", max_length=18, default="#0f172a",
                                   help_text="Color oscuro para textos principales. Ej: #0f172a")

    # Tipografía y Tamaño de Fuente
    tipografia_principal = models.CharField(
        "Tipo de Letra Principal (Cuerpo y Menús)",
        max_length=40,
        choices=TipografiaPrincipal.choices,
        default=TipografiaPrincipal.PLUS_JAKARTA,
        help_text="Familia tipográfica para párrafos, menús y navegación."
    )
    tipografia_titulos = models.CharField(
        "Tipo de Letra para Títulos (Encabezados)",
        max_length=40,
        choices=TipografiaTitulos.choices,
        default=TipografiaTitulos.LORA,
        help_text="Familia tipográfica para títulos principales H1, H2, H3."
    )
    tamano_letra = models.CharField(
        "Tamaño de Letra del Sitio",
        max_length=20,
        choices=TamanoLetra.choices,
        default=TamanoLetra.NORMAL,
        help_text="Escala proporcional de fuentes de todo el portal público."
    )

    class Meta:
        db_table = "CONFIGURACION_APARIENCIA"
        verbose_name = "Apariencia, Tipografía y Colores"
        verbose_name_plural = "Apariencia, Tipografía y Colores"

    def __str__(self):
        return "Configuración de Apariencia de la Web"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @property
    def css_fuente_principal(self) -> str:
        fuentes = {
            "plus_jakarta_sans": "'Plus Jakarta Sans', system-ui, -apple-system, sans-serif",
            "inter": "'Inter', system-ui, -apple-system, sans-serif",
            "outfit": "'Outfit', system-ui, -apple-system, sans-serif",
            "roboto": "'Roboto', system-ui, -apple-system, sans-serif",
            "montserrat": "'Montserrat', system-ui, -apple-system, sans-serif",
            "open_sans": "'Open Sans', system-ui, -apple-system, sans-serif",
            "merriweather": "'Merriweather', Georgia, serif",
        }
        return fuentes.get(self.tipografia_principal, fuentes["plus_jakarta_sans"])

    @property
    def css_fuente_titulos(self) -> str:
        fuentes = {
            "lora": "'Lora', Georgia, serif",
            "plus_jakarta_sans": "'Plus Jakarta Sans', system-ui, sans-serif",
            "playfair": "'Playfair Display', Georgia, serif",
            "outfit": "'Outfit', system-ui, sans-serif",
            "montserrat": "'Montserrat', system-ui, sans-serif",
            "merriweather": "'Merriweather', Georgia, serif",
        }
        return fuentes.get(self.tipografia_titulos, fuentes["lora"])

    @property
    def css_escala_fuente(self) -> str:
        escalas = {
            "compacto": "92%",
            "normal": "100%",
            "comodo": "108%",
            "grande": "116%",
            "muy_grande": "125%",
        }
        return escalas.get(self.tamano_letra, "100%")

    @property
    def css_tamano_base(self) -> str:
        tamanos = {
            "compacto": "14.5px",
            "normal": "16px",
            "comodo": "17.2px",
            "grande": "18.5px",
            "muy_grande": "20px",
        }
        return tamanos.get(self.tamano_letra, "16px")

