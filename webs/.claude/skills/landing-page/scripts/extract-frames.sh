#!/usr/bin/env bash
# =============================================================
#  extract-frames.sh — Pre-extrae los frames de un video para
#  el efecto scroll-canvas, en BUILD TIME (no en el navegador).
#
#  Por qué: extraer frames en el navegador del usuario lo hace
#  esperar y consume su batería/RAM. Pre-extraídos como WebP, el
#  visitante solo descarga imágenes ligeras → carga instantánea.
#
#  Uso:
#    ./extract-frames.sh <video.mp4> [fps] [ancho]
#  Ejemplo:
#    ./extract-frames.sh assets/video.mp4 30 854
#
#  Requisitos: ffmpeg instalado (sudo pacman -S ffmpeg)
# =============================================================
set -euo pipefail

VIDEO="${1:?Pasa la ruta del video: ./extract-frames.sh video.mp4}"
FPS="${2:-30}"        # 24-30 suele bastar. Más = más suave y más peso.
WIDTH="${3:-854}"     # Ancho de salida. Alto se calcula manteniendo proporción.
OUTDIR="frames"
QUALITY=80            # Calidad WebP (0-100). 80 = buen balance peso/calidad.

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg no está instalado. Instala con: sudo pacman -S ffmpeg" >&2
  exit 1
fi

echo "→ Extrayendo frames de '$VIDEO'"
echo "  fps=$FPS  ancho=${WIDTH}px  calidad=$QUALITY  destino=$OUTDIR/"

rm -rf "$OUTDIR"
mkdir -p "$OUTDIR"

ffmpeg -hide_banner -loglevel error -stats \
  -i "$VIDEO" \
  -vf "scale=${WIDTH}:-2,fps=${FPS}" \
  -q:v "$QUALITY" \
  "$OUTDIR/f_%04d.webp"

COUNT=$(find "$OUTDIR" -name 'f_*.webp' | wc -l)
SIZE=$(du -sh "$OUTDIR" | cut -f1)

echo ""
echo "✓ Listo: $COUNT frames generados en $OUTDIR/ (peso total: $SIZE)"
echo ""
echo "Siguiente paso: en app.js, en vez de extractFrames() sobre <video>,"
echo "precarga f_0001.webp ... f_${COUNT}.webp como ImageBitmap y dibuja por índice."
echo "Genera el manifiesto con:  ls frames/*.webp | wc -l   →  total de frames"
