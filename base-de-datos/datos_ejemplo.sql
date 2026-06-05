-- ===========================================================================
--  Athena — Datos de ejemplo (Oracle)
-- ===========================================================================
--  Ejemplo de la jerarquía:  2026 → Período 1 → 6°A → Matemáticas → guía
--
--  Nota: en desarrollo es más cómodo cargar datos demo con:
--      python manage.py seed_demo
--  Este script es el equivalente en SQL puro para Oracle.
--
--  RUTA_ARCHIVO debe apuntar al objeto real en Object Storage. Aquí van rutas
--  de ejemplo; reemplázalas por las reales tras subir los archivos.
-- ===========================================================================

-- Año y jerarquía
INSERT INTO ANIOS (anio, activo) VALUES (2026, 1);

INSERT INTO PERIODOS (anio_id, numero, nombre)
VALUES ((SELECT id FROM ANIOS WHERE anio = 2026), 1, 'Primer período');

INSERT INTO CURSOS (periodo_id, nombre, nivel)
VALUES ((SELECT id FROM PERIODOS WHERE anio_id = (SELECT id FROM ANIOS WHERE anio = 2026) AND numero = 1),
        '6°A', 'Secundaria');

INSERT INTO MATERIAS (curso_id, nombre)
VALUES ((SELECT id FROM CURSOS WHERE nombre = '6°A'), 'Matemáticas');

INSERT INTO GUIAS (materia_id, titulo, descripcion, RUTA_ARCHIVO, fecha_publicacion)
VALUES ((SELECT id FROM MATERIAS WHERE nombre = 'Matemáticas'),
        'Guía 1 — Números enteros',
        'Repaso de operaciones con números enteros.',
        'guias/guia-1-numeros-enteros.pdf',
        DATE '2026-02-15');

-- Secciones de texto (la home)
INSERT INTO SECCIONES (clave, titulo, contenido)
VALUES ('nombre_sitio', 'Nombre del Colegio', 'Edita este texto desde el panel del rector.');
INSERT INTO SECCIONES (clave, titulo, contenido)
VALUES ('mision', 'Misión', 'Texto de la misión institucional (editable por el rector).');
INSERT INTO SECCIONES (clave, titulo, contenido)
VALUES ('vision', 'Visión', 'Texto de la visión institucional (editable por el rector).');
INSERT INTO SECCIONES (clave, titulo, contenido)
VALUES ('contacto', 'Contacto', 'Dirección, teléfono y correo del colegio.');

-- Noticia
INSERT INTO NOTICIAS (titulo, cuerpo, fecha_publicacion, activo)
VALUES ('Bienvenida al año escolar 2026',
        'Damos la bienvenida a toda la comunidad educativa al nuevo año.',
        SYSTIMESTAMP, 1);

-- Video (YouTube)
INSERT INTO VIDEOS (titulo, youtube_url, descripcion, fecha)
VALUES ('Video institucional', 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
        'Presentación del colegio.', SYSDATE);

COMMIT;
