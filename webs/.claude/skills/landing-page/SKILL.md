---
name: landing-page
description: Genera landing pages y sitios scrollytelling con el estilo de la casa (Casa de Software). Estética editorial dark, tipografía esculpida, video protagonista en scroll-canvas, gráficos SVG inline, animaciones por scroll con GSAP. Úsalo al arrancar cualquier web de cliente o cuando se pida una landing, sitio one-page, o página de producto con scroll cinematográfico.
---

# Landing page — estilo de la casa

Genera webs scrollytelling de alto nivel siguiendo el sistema de diseño de
Código Beta. NO plantillas genéricas. Cada web arranca de este patrón y se
ajusta a la marca del cliente (su CLAUDE.md local manda sobre colores y copy).

## Filosofía de diseño (definir ANTES de codear)
1. **Editorial, no corporativo.** Tipografía serif display + sans técnica + mono para detalles.
2. **Un solo color de acento**, usado con moderación. El resto es escala de grises cálidos sobre fondo oscuro.
3. **El video/visual es protagonista**, fijo de fondo, dirigido por el scroll.
4. **Secciones alternadas** izquierda/derecha que se sienten como páginas de una revista.
5. **Gráficos con sentido**, no decorativos: SVG inline (radar, líneas, barras) que comparan o explican.

## Stack
- HTML + CSS + JS vanilla. Sin framework.
- GSAP 3.12 + ScrollTrigger (animaciones), Lenis 1.1 (scroll suave). Vía CDN jsdelivr.
- Google Fonts con preconnect. Default: Instrument Serif (display) + Geist (sans) + Geist Mono.
- Estructura: index.html / styles.css / app.js + assets/.

## Tokens base (ajustar al cliente)
```css
:root {
  --bg: #0a0a0a;          /* fondo */
  --bg-deep: #050505;
  --ink: #f4f1ea;         /* blanco hueso cálido */
  --ink-dim: #8a8680;
  --ink-faint: #45433f;
  --rule: #1a1a1a;
  --accent: #d4ff3a;      /* UN acento de alto voltaje, usado con moderación */
  --ease-out-expo: cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);
  --grid-gutter: clamp(20px, 3vw, 48px);
  --page-pad: clamp(24px, 4vw, 64px);
}
::selection { background: var(--accent); color: var(--bg); }
```

## Estructura de página (esqueleto)
```
loader (con % y métricas técnicas)
stage fija (video + canvas + veil)
chrome (logo arriba)
dock de navegación (glass, horizontal, con separadores)
progress bar (barra de scroll arriba)
main:
  hero (título a dos líneas en split-line + manifiesto)
  sección 01 left  — el encuentro / intro
  sección 02 right — quiénes somos  [+ gráfico radar]
  sección 03 left  — filosofía       [+ gráfico líneas calidad/tiempo]
  sección 04 right xtall — proceso (steps I/II/III) [+ gráfico barras timeline]
  ...secciones intermedias del cliente...
  sección — precios/pago (bloques 50/50)
  sección — FAQ (la entrevista)
  sección — CTA (canales: agendar/WhatsApp/correo)
  closing (cierre + footer)
chat AI flotante (fab + panel)
```

## Tipos de sección (clases)
- `.section--left` / `.section--right` — alterna el lado del panel.
- `.section--tall` — altura estándar de capítulo.
- `.section--xtall` — para secciones con más contenido (ej. proceso).
- Cada sección lleva `data-rail-target="N"` (índice para sincronizar dock y video).

## Animaciones (atributo data-anim)
Cuatro tipos, aplicados por scroll vía GSAP + ScrollTrigger:
- `fade-blur` — aparece desenfocado y enfoca. Para títulos.
- `rise` — sube y aparece. Para cuerpo de texto (el más usado).
- `scale-up` — escala desde 0.9. Para destacar bloques.
- `clip-circle` — revela con máscara circular. Para frases "pull" importantes.

Ampliar el catálogo según cliente (slide-in lateral, mask wipe, contador numérico,
typewriter, parallax por capas) — pero mantener consistencia: máx 4-5 tipos por sitio.

## Video en scroll-canvas (CRÍTICO — hacerlo bien)
El video NO se reproduce solo. Se dibuja sobre <canvas> según la posición de scroll.

**Regla de oro: pre-extraer frames en build time, NO en el navegador del usuario.**

Pipeline correcto:
1. ffmpeg parte el video en secuencia WebP optimizada (no extraer en runtime):
   `ffmpeg -i video.mp4 -vf "scale=854:-1,fps=30" -q:v 80 frames/f_%04d.webp`
   Ajustar fps según fluidez deseada (24-30 suele bastar; más = más suave y más peso).
2. Precargar las imágenes como ImageBitmap (dibujo GPU-rápido).
3. Mapear scroll → índice de frame. Usar smoothstep entre anclas de sección
   para que cada capítulo tenga su ritmo (no scroll lineal plano).
4. Blending opcional entre frame A y B (mix 0-1) para suavidad sub-frame.

Esto elimina la espera del loader y funciona en celulares lentos.
NUNCA seek directo sobre <video> (la latencia entre keyframes MP4 causa stutter).

## Gráficos SVG inline
Dibujar a mano con <svg>, animados al entrar en viewport. Patrones del sistema:
- **Radar** (hexagonal): comparar "nosotros vs ellos" en N ejes.
- **Líneas**: evolución en el tiempo (ej. calidad sostenida vs degradación).
- **Barras segmentadas**: distribución (ej. esfuerzo por fase, con --w en %).
Siempre con figcaption (FIG. NN + título) y leyenda. El gráfico explica, no decora.

## Accesibilidad y rendimiento
- Respetar `prefers-reduced-motion`: desactivar scroll-canvas y animaciones pesadas.
- alt en imágenes, aria-label en botones de ícono, aria-hidden en decorativos.
- WebP para todo lo rasterizado. Fuentes con preconnect + display=swap.
- Lazy-load de secciones pesadas. El primer paint no debe esperar al video.

## Referencia
El proyecto Código Beta es la implementación de referencia de este patrón
(index.html / styles.css / app.js). Consultarlo para ver el sistema completo
en funcionamiento antes de improvisar uno nuevo.
