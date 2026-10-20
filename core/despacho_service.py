import json
import os
import urllib.request
from datetime import date
from typing import Dict, Any
from django.utils import timezone


def generar_siguiente_radicado(tipo: str) -> str:
    from core.models import ComunicadoOficial

    anio = date.today().year
    prefijos = {
        "circular": "CIRCULAR",
        "comunicado": "COMUNICADO",
        "resolucion": "RESOLUCIÓN RECTORAL",
        "citacion": "CITACIÓN DIRECTIVA",
    }
    pref = prefijos.get(tipo, "CIRCULAR")
    total_tipo_anio = ComunicadoOficial.objects.filter(
        tipo=tipo,
        fecha_emision__year=anio
    ).count() + 1

    return f"{pref} No. {total_tipo_anio:03d} - {anio}"


def redactar_comunicado_ia(
    tipo: str,
    asunto: str,
    destinatario: str,
    instrucciones: str = "",
    radicado: str = "",
    fecha: str = "",
) -> Dict[str, str]:
    """Genera mediante Qwen 3.8 27B un documento formal institucional escolar
    con membrete, considerandos legales y versión optimizada para WhatsApp."""
    api_key = os.getenv("GROQ_API_KEY")
    hoy_str = fecha or date.today().strftime("%d de %B de %Y")
    radicado_str = radicado or generar_siguiente_radicado(tipo)

    system_prompt = (
        "Eres el Asesor Jurídico y Secretario General de Despacho Rectoral de la Institución Educativa Departamental "
        "Complejo Educativo Integral Sopó (I.E.D. CEIS), en Sopó, Cundinamarca, Colombia.\n"
        "Rector: Lic. Juan Carlos Aguirre Nieto.\n"
        "Modelo Pedagógico: Sistema Educativo Relacional (SERC).\n"
        "Misión: Garantizar una educación pública de excelencia, paz y progreso para niños, niñas y jóvenes de Sopó.\n"
        "Tu misión es redactar comunicaciones escolares impecables, con lenguaje formal institucional colombiano, "
        "estricto rigor jurídico (Ley 115 de 1994, Decreto 1290 de 2009, Ley 1620 de Convivencia Escolar), "
        "claridad total para padres y familias, y CERO emojis o informalidades.\n\n"
        "Debes responder ÚNICAMENTE un objeto JSON válido con exactamente dos campos:\n"
        "{\n"
        '  "titulo": "Título formal conciso del documento",\n'
        '  "cuerpo_html": "<p>Contenido estructurado en párrafos HTML...</p>",\n'
        '  "resumen_whatsapp": "Texto formateado para WhatsApp con *negritas*, viñetas (-) y llamado a la acción formal sin emojis."\n'
        "}"
    )

    user_prompt = (
        f"Tipo de documento: {tipo.upper()}\n"
        f"Número de radicado: {radicado_str}\n"
        f"Fecha: {hoy_str}\n"
        f"Destinatario: {destinatario}\n"
        f"Asunto central: {asunto}\n"
        f"Directrices e instrucciones específicas a incorporar:\n{instrucciones or 'Redactar con base en el asunto y los lineamientos oficiales del CEIS.'}\n\n"
        "Estructura requerida para cuerpo_html:\n"
        "1. Saludo institucional formal.\n"
        "2. Fundamento legal o considerandos (según corresponda por el asunto).\n"
        "3. Desarrollo de directrices numeradas (puntos 1, 2, 3...) con fechas, requisitos, horarios y compromisos.\n"
        "4. Enlaces de referencia institucional recomendados: mencionar /documentos/ para guías o /consulta-notas/ para informes.\n"
        "5. Cierre formal institucional.\n"
        "Para resumen_whatsapp: redactar de forma sintética (máximo 12 líneas), clara y directa, con el número de radicado, asunto, fechas clave y aviso de consulta web."
    )

    if api_key:
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.25,
            "max_tokens": 1200,
        }
        try:
            req = urllib.request.Request(
                "https://api.groq.com/openai/v1/chat/completions",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0",
                },
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content_str = data["choices"][0]["message"]["content"].strip()
                parsed = json.loads(content_str)
                return {
                    "titulo": parsed.get("titulo", asunto),
                    "cuerpo_html": parsed.get("cuerpo_html", ""),
                    "resumen_whatsapp": parsed.get("resumen_whatsapp", ""),
                    "radicado": radicado_str,
                }
        except Exception:
            pass

    # Fallback determinista institucional
    titulo_fb = f"{asunto}"
    cuerpo_fb = (
        f"<p>El Despacho Rectoral del I.E.D. Complejo Educativo Integral Sopó (CEIS), en ejercicio de sus facultades "
        f"legales conferidas por la Ley General de Educación (Ley 115 de 1994) y el Decreto 1290 de 2009, se permite "
        f"comunicar a {destinatario.lower()}:</p>"
        f"<p><strong>1. Asunto Oficial:</strong> {asunto}.</p>"
        f"<p><strong>2. Disposiciones Institucionales:</strong> {instrucciones or 'Se solicita dar cabal cumplimiento a las directrices académicas y de convivencia establecidas en el Manual Institucional.'}</p>"
        f"<p><strong>3. Canales Oficiales:</strong> La comunidad educativa puede consultar la documentación y soportes en la plataforma web institucional "
        f"<a href='/documentos/'>https://athena.maxstudio.lat/documentos/</a>.</p>"
        f"<p>Dada en Sopó, Cundinamarca, a los {hoy_str}.</p>"
    )
    wapp_fb = (
        f"*I.E.D. CEIS SOPÓ — {radicado_str}*\n\n"
        f"*Destinatario:* {destinatario}\n"
        f"*Asunto:* {asunto}\n\n"
        f"{instrucciones or 'Se informa a la comunidad sobre las disposiciones institucionales vigentes.'}\n\n"
        f"Consulte el documento oficial y calificaciones en: https://athena.maxstudio.lat/documentos/"
    )
    return {
        "titulo": titulo_fb,
        "cuerpo_html": cuerpo_fb,
        "resumen_whatsapp": wapp_fb,
        "radicado": radicado_str,
    }
