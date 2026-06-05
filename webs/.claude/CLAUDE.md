# Webs — Casa de Software

## Qué es esto
Subcarpeta de proyectos web de clientes. Cada cliente vive en su propia
subcarpeta dentro de aquí, con su propio CLAUDE.md (marca, colores, alcance).
Las skills de esta carpeta (frontend-design, theme-factory, canvas-design,
landing-page) están disponibles para todos los proyectos de cliente.

## Stack base de webs
- HTML + CSS + JS vanilla para landings/sitios. Sin framework salvo que el cliente lo exija.
- Animación: GSAP + ScrollTrigger. Scroll suave: Lenis.
- Tipografía vía Google Fonts. Diseño dark editorial por defecto (ver skill landing-page).
- Todo el sitio debe correr abriendo index.html — sin build step para landings simples.

## Cómo arranca un cliente nuevo
1. Crear subcarpeta con el nombre del cliente.
2. Dentro, su `.claude/CLAUDE.md` con: marca, paleta, fuentes, secciones, alcance.
3. Invocar la skill `landing-page` para generar el esqueleto con el estilo de la casa.
4. No empezar a codear el diseño hasta que ese CLAUDE.md de cliente exista.

## Multimedia en proyectos web
- Claude Code NO genera video ni imágenes con IA (no accede a Google Vertex).
- Cuando un proyecto necesite video (Veo 3) o imágenes (Nano Banana 2, Imagen 4):
  → delegar a Hermes Agent (distrito Media Factory) para generarlos vía Vertex.
  → Hermes devuelve los assets; Claude Code construye la web con ellos.

## Video en scroll (efecto cinematográfico)
- NUNCA usar <video> directo para efectos scroll-driven (el video va a su ritmo, no al del scroll).
- Técnica correcta: secuencia de fotogramas sobre <canvas>, dibujando el frame según posición de scroll.
- PRE-EXTRAER los frames en build time (ffmpeg → WebP), NO extraerlos en el navegador del usuario.
  Extraer en runtime hace esperar al visitante y consume su batería/RAM.
- Detalle de implementación → skill `landing-page`.

## Convenciones
- Cada cliente es una carpeta aislada. No mezclar código ni assets entre clientes.
- Optimizar peso: imágenes en WebP, video comprimido, fuentes con preconnect.
- Accesibilidad mínima: alt en imágenes, aria-labels en botones de ícono, respetar prefers-reduced-motion.
- El cliente recibe el código fuente completo. README mínimo para correr/desplegar.

## Lo que NO se hace aquí
- No reusar credenciales ni datos entre clientes.
- No sobre-construir: sin login, DB ni features que el cliente no pidió.
- No degradados morados genéricos ni fuente Inter por defecto (usar el sistema de diseño real).
