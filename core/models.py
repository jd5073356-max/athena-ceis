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
        SOFTWARE = "software", "Software Institucional"  # plataformas y sistemas de software

    clave = models.SlugField("Clave", max_length=60, unique=True,
                             help_text="Identificador interno. Ej.: mision, vision, prae.")
    titulo = models.CharField("Título", max_length=160)
    contenido = models.TextField("Contenido", blank=True)
    categoria = models.CharField("Categoría", max_length=20,
                                 choices=Categoria.choices, default=Categoria.HOME)
    orden = models.PositiveIntegerField("Orden", default=0,
                                        help_text="Orden dentro de su categoría.")
    enlace_externo = models.URLField("Enlace a la plataforma", blank=True,
                                     help_text="Si se llena, la página muestra el botón 'Abrir plataforma'.")
    grupo = models.CharField("Grupo", max_length=80, blank=True,
                             help_text="Opcional. Agrupa proyectos en el listado. Ej.: Software de Inclusión.")

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
    """Personalización dinámica integral del portal escolar: marca, paleta, tipografía,
    tokens de diseño, anuncios y datos oficiales de contacto (gestión desde el admin)."""

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

    class RadioBordes(models.TextChoices):
        RECTO = "recto", "Sobrio / Recto (4px)"
        EQUILIBRADO = "equilibrado", "Equilibrado (12px — Predeterminado)"
        REDONDEADO = "redondeado", "Redondeado / Moderno (20px)"

    class IntensidadSombras(models.TextChoices):
        PLANO = "plano", "Plano / Minimalista (Sin sombras)"
        SUTIL = "sutil", "Sutil (Predeterminado — Elevación suave)"
        PROFUNDO = "profundo", "Profundo (Sombras con relieve marcado)"

    class EstiloMenu(models.TextChoices):
        SOLIDO = "solido", "Color Sólido Institucional (Predeterminado)"
        CRISTAL = "cristal", "Cristal / Glassmorphism traslúcido"
        CLARO = "claro", "Fondo Blanco / Claro"

    class AvisoTipo(models.TextChoices):
        INFORMATIVO = "informativo", "Informativo (Azul institucional / Teal)"
        ALERTA = "alerta", "Alerta / Atención (Dorado ámbar)"
        URGENTE = "urgente", "Urgente / Importante (Rojo institucional)"

    # Identidad y Marca
    logo_institucional = models.FileField(
        "Escudo / Logo Principal",
        upload_to="branding/",
        blank=True,
        null=True,
        help_text="Imagen del escudo o logo oficial (PNG, SVG, JPG, WebP). Si se deja vacío se usa el escudo por defecto."
    )
    favicon_institucional = models.FileField(
        "Favicon Institucional",
        upload_to="branding/",
        blank=True,
        null=True,
        help_text="Icono pequeño para la pestaña del navegador (PNG, ICO). Si se deja vacío se usa el escudo por defecto."
    )
    portada_hero = models.FileField(
        "Imagen de Portada Principal (Hero)",
        upload_to="branding/",
        blank=True,
        null=True,
        help_text="Fotografía destacada para el banner principal. Si se deja vacío se usa la fotografía por defecto."
    )
    lema_institucional = models.CharField(
        "Lema Institucional",
        max_length=160,
        default="Paz, Educación y Progreso",
        help_text="Lema oficial que aparece debajo del nombre en cabecera y pie de página."
    )
    titulo_hero = models.CharField(
        "Título Principal del Hero",
        max_length=160,
        default="I.E.D. CEIS Sopó",
        help_text="Título principal visible en el banner de bienvenida."
    )
    subtitulo_hero = models.CharField(
        "Subtítulo del Hero",
        max_length=255,
        default="Complejo Educativo Integral Sopó · Formando líderes con calidad y sentido humano.",
        help_text="Texto descriptivo visible en el banner principal."
    )

    # Paleta de Colores
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

    # Tokens de Diseño
    radio_bordes = models.CharField(
        "Estilo de Bordes y Esquinas",
        max_length=20,
        choices=RadioBordes.choices,
        default=RadioBordes.EQUILIBRADO,
        help_text="Curvatura de esquinas en botones, tarjetas y acordeones."
    )
    intensidad_sombras = models.CharField(
        "Intensidad de Sombras y Relieve",
        max_length=20,
        choices=IntensidadSombras.choices,
        default=IntensidadSombras.SUTIL,
        help_text="Profundidad de sombreado en tarjetas y contenedores elevados."
    )
    estilo_menu = models.CharField(
        "Estilo de la Barra de Navegación",
        max_length=20,
        choices=EstiloMenu.choices,
        default=EstiloMenu.SOLIDO,
        help_text="Tratamiento visual de la barra de menú superior."
    )

    # Barra de Avisos
    aviso_activo = models.BooleanField(
        "Activar Barra de Aviso Superior",
        default=False,
        help_text="Muestra una franja destacada de anuncio en la parte superior del portal."
    )
    aviso_texto = models.CharField(
        "Texto del Aviso",
        max_length=255,
        blank=True,
        help_text="Mensaje del anuncio. Ej: Inscripciones abiertas para el año escolar 2026."
    )
    aviso_tipo = models.CharField(
        "Tipo de Aviso",
        max_length=20,
        choices=AvisoTipo.choices,
        default=AvisoTipo.INFORMATIVO,
        help_text="Estilo visual y color de la franja de anuncio."
    )
    aviso_enlace = models.CharField(
        "Enlace del Aviso (Opcional)",
        max_length=255,
        blank=True,
        help_text="Ruta interna o enlace web hacia donde redirige el aviso."
    )
    aviso_texto_enlace = models.CharField(
        "Texto del Botón/Enlace (Opcional)",
        max_length=60,
        blank=True,
        default="Más información",
        help_text="Etiqueta visible del botón de enlace del aviso."
    )

    # Contacto y Canales Oficiales
    telefono_contacto = models.CharField(
        "Teléfono Institucional",
        max_length=40,
        default="310 871 0141",
        help_text="Teléfono visible en pie de página y datos de contacto."
    )
    whatsapp_contacto = models.CharField(
        "Número de WhatsApp",
        max_length=40,
        default="310 871 0141",
        help_text="Número para enlace directo de WhatsApp institucional."
    )
    email_contacto = models.EmailField(
        "Correo Electrónico Oficial",
        default="iedceis@gmail.com",
        help_text="Correo de secretaría académica y atención a la comunidad."
    )
    direccion_contacto = models.CharField(
        "Dirección Física",
        max_length=160,
        default="Carrera 10 No. 1-31, Sopó, Cundinamarca",
        help_text="Dirección de la sede principal."
    )
    horario_atencion = models.CharField(
        "Horario de Atención",
        max_length=120,
        default="Martes, miércoles y jueves de 8:00 a.m. a 12:00 m.",
        help_text="Horario presencial de secretaría académica."
    )
    red_facebook = models.URLField("Enlace a Facebook Oficial", blank=True, help_text="Página de Facebook institucional.")
    red_youtube = models.URLField("Canal de YouTube Oficial", blank=True, help_text="Canal de YouTube del colegio.")
    red_instagram = models.URLField("Enlace a Instagram Oficial", blank=True, help_text="Perfil de Instagram institucional.")

    # Asistente Virtual Athena
    athena_activo = models.BooleanField(
        "Habilitar Asistente Athena en Web Pública",
        default=True,
        help_text="Muestra u oculta la asesora virtual interactiva en la web pública."
    )
    athena_nombre_visible = models.CharField(
        "Nombre Visible de la Asesora",
        max_length=60,
        default="Athena",
        help_text="Nombre que se muestra en la cabecera del diálogo de chat."
    )
    athena_mensaje_bienvenida = models.TextField(
        "Mensaje de Bienvenida Inicial",
        default="Saludos. Soy Athena, la asesora institucional del I.E.D. CEIS. ¿En qué puedo orientarte hoy?",
        help_text="Primer mensaje que visualiza el usuario al desplegar el chat."
    )

    class Meta:
        db_table = "CONFIGURACION_APARIENCIA"
        verbose_name = "Configuración Institucional y Apariencia"
        verbose_name_plural = "Configuración Institucional y Apariencia"

    def __str__(self):
        return "Configuración Institucional del Portal"

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

    @property
    def css_radius_sm(self) -> str:
        return {"recto": "2px", "equilibrado": "8px", "redondeado": "12px"}.get(self.radio_bordes, "8px")

    @property
    def css_radius_md(self) -> str:
        return {"recto": "4px", "equilibrado": "12px", "redondeado": "20px"}.get(self.radio_bordes, "12px")

    @property
    def css_radius_lg(self) -> str:
        return {"recto": "6px", "equilibrado": "16px", "redondeado": "28px"}.get(self.radio_bordes, "16px")

    @property
    def css_sombra_sm(self) -> str:
        return {
            "plano": "none",
            "sutil": "0 2px 8px rgba(10,25,49,0.04)",
            "profundo": "0 4px 14px rgba(10,25,49,0.09)",
        }.get(self.intensidad_sombras, "0 2px 8px rgba(10,25,49,0.04)")

    @property
    def css_sombra_md(self) -> str:
        return {
            "plano": "none",
            "sutil": "0 10px 25px -5px rgba(10,25,49,0.08), 0 8px 10px -6px rgba(10,25,49,0.04)",
            "profundo": "0 16px 36px -4px rgba(10,25,49,0.16), 0 10px 16px -4px rgba(10,25,49,0.08)",
        }.get(self.intensidad_sombras, "0 10px 25px -5px rgba(10,25,49,0.08)")

    @property
    def css_sombra_lg(self) -> str:
        return {
            "plano": "none",
            "sutil": "0 20px 35px -10px rgba(10,25,49,0.15)",
            "profundo": "0 28px 50px -8px rgba(10,25,49,0.26)",
        }.get(self.intensidad_sombras, "0 20px 35px -10px rgba(10,25,49,0.15)")

    @property
    def css_menu_bg(self) -> str:
        return {
            "solido": "var(--azul-claro)",
            "cristal": "rgba(21, 48, 91, 0.88)",
            "claro": "#ffffff",
        }.get(self.estilo_menu, "var(--azul-claro)")

    @property
    def css_menu_texto(self) -> str:
        return {
            "solido": "#f1f5f9",
            "cristal": "#ffffff",
            "claro": "var(--azul)",
        }.get(self.estilo_menu, "#f1f5f9")

    @property
    def css_menu_backdrop(self) -> str:
        return {
            "solido": "none",
            "cristal": "blur(14px)",
            "claro": "none",
        }.get(self.estilo_menu, "none")


# ===========================================================================
#  Sistema de Seguimiento Académico y Boletines SERC
# ===========================================================================
class Estudiante(models.Model):
    """Estudiante matriculado en la institución."""
    documento = models.CharField("Número de documento", max_length=20, unique=True, db_index=True,
                                 help_text="Número de T.I. o documento de identidad.")
    tipo_documento = models.CharField("Tipo de documento", max_length=40, default="Tarjeta de Identidad")
    nombres = models.CharField("Nombres", max_length=100)
    apellidos = models.CharField("Apellidos", max_length=100)
    grado = models.CharField("Grado", max_length=30, default="UNDECIMO", help_text="Ej: SEXTO, DECIMO, UNDECIMO")
    curso = models.CharField("Curso", max_length=10, db_index=True, help_text="Ej: 601, 702, 1101")
    acudiente = models.CharField("Acudiente", max_length=150, blank=True)
    telefono_acudiente = models.CharField("Teléfono acudiente", max_length=30, blank=True)
    director_grupo = models.CharField("Director(a) de Grupo", max_length=150, default="ROJAS GUTIERREZ LILIANA ASTRID")
    activo = models.BooleanField("Activo", default=True)

    class Meta:
        db_table = "ESTUDIANTES"
        verbose_name = "Estudiante"
        verbose_name_plural = "Estudiantes"
        ordering = ["curso", "apellidos", "nombres"]

    def __str__(self):
        return f"{self.apellidos} {self.nombres} ({self.curso})"

    @property
    def nombre_completo(self) -> str:
        return f"{self.apellidos} {self.nombres}".strip()


class InformeValorativo(models.Model):
    """Boletín oficial de evaluación SERC (Sistema Educativo Relacional Cundinamarca)."""
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, related_name="informes",
                                   verbose_name="Estudiante")
    anio_lectivo = models.PositiveIntegerField("Año lectivo", default=2026)
    periodo_actual = models.PositiveSmallIntegerField("Período actual", default=3,
                                                      choices=[(1, "I"), (2, "II"), (3, "III"), (4, "IV")])
    datos_academicos = models.JSONField("Datos Académicos SERC", default=dict,
                                        help_text="Estructura JSON con áreas, asignaturas, etapas SERC y notas.")
    datos_convivencia = models.JSONField("Datos de Convivencia", default=dict,
                                         help_text="Fallas, retardos, uniforme y valoración de convivencia.")
    observaciones_academicas = models.TextField("Observaciones Académicas", blank=True,
                                                default="El estudiante debe presentar el desarrollo completo de las guías no alcanzadas en el menor tiempo posible.\nA la fecha, el aprendiz SENA ha cumplido con la entrega de las evidencias propuestas.")
    observaciones_convivenciales = models.TextField("Observaciones Convivenciales", blank=True,
                                                    default="La institución agradece su colaboración en las campañas de mejora .\nFelicitaciones por su aporte a la convivencia institucional.")
    tecnico_sena = models.CharField("Técnico SENA", max_length=20, default="A",
                                    help_text="Valoración SENA: A (Aprobado), BS (Básico), etc.")
    fecha_emision = models.DateField("Fecha de emisión", auto_now=True)

    class Meta:
        db_table = "INFORMES_VALORATIVOS"
        verbose_name = "Informe Valorativo SERC"
        verbose_name_plural = "Informes Valorativos SERC"
        unique_together = ("estudiante", "anio_lectivo")

    def __str__(self):
        return f"Informe {self.anio_lectivo} - {self.estudiante.nombre_completo} ({self.estudiante.curso})"


class DatasetAnalisis(models.Model):
    """Conjunto de datos estructurados externo para análisis (ICFES, Evaluar para Avanzar, caracterización)."""
    CATEGORIAS = [
        ("icfes", "Pruebas ICFES / Saber 11°"),
        ("evaluar_avanzar", "Evaluar para Avanzar"),
        ("socioeconomico", "Caracterización Socioeconómica / SISBEN"),
        ("diagnostica", "Pruebas Diagnósticas Internas"),
        ("convivencia", "Clima Escolar y Convivencia"),
        ("otro", "Otro Análisis Institucional"),
    ]

    titulo = models.CharField("Título del Análisis", max_length=180, help_text="Ej: Resultados Históricos Saber 11° (2022-2025)")
    categoria = models.CharField("Categoría", max_length=40, choices=CATEGORIAS, default="icfes")
    archivo = models.FileField("Archivo de Datos (Excel o CSV)", upload_to="datasets/", blank=True, null=True)
    descripcion = models.TextField("Descripción / Contexto", blank=True, help_text="Notas o propósito de la evaluación.")
    datos_normalizados = models.JSONField("Datos Estructurados", default=dict, blank=True,
                                         help_text="Matriz JSON con columnas, filas procesadas, resúmenes y deltas anuales.")
    diagnostico_ia = models.TextField("Diagnóstico Ejecutivo Athena IA", blank=True,
                                      help_text="Síntesis directiva generada por IA con puntos críticos y recomendaciones.")
    fecha_creacion = models.DateTimeField("Fecha de creación", auto_now_add=True)
    fecha_actualizacion = models.DateTimeField("Última actualización", auto_now=True)

    class Meta:
        db_table = "DATASETS_ANALISIS"
        verbose_name = "Dataset de Análisis"
        verbose_name_plural = "Datasets de Análisis"
        ordering = ["-fecha_creacion"]

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"


