import csv
import io
import json
import os
import re
import urllib.request
from collections import defaultdict
from typing import Any, Dict, List, Tuple


_MAPA_SERC_NUMERICO = {
    "SUPERIOR": 95.0,
    "ALTO": 82.0,
    "BÁSICO": 68.0,
    "BASICO": 68.0,
    "BAJO": 45.0,
}


def _limpiar_numero(val: Any) -> float | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s:
        return None
    s_upper = s.upper()
    if s_upper in _MAPA_SERC_NUMERICO:
        return _MAPA_SERC_NUMERICO[s_upper]
    s_clean = s.replace(" ", "").replace(",", ".")
    try:
        return float(s_clean)
    except ValueError:
        return None


def leer_filas_archivo(file_obj_or_path, filename: str) -> List[List[Any]]:
    """Lee filas de un archivo Excel (.xlsx, .xls) o CSV y las devuelve como lista de listas.
    Si el Excel tiene múltiples hojas con estructura similar (ej. sábana por cursos), las consolida."""
    ext = os.path.splitext(filename)[1].lower()
    filas = []

    if ext in (".xlsx", ".xlsm"):
        import openpyxl
        wb = openpyxl.load_workbook(file_obj_or_path, data_only=True)
        if len(wb.sheetnames) > 1:
            header_global = None
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                sheet_rows = [
                    list(r) for r in sheet.iter_rows(values_only=True)
                    if any(cell is not None and str(cell).strip() != "" for cell in r)
                ]
                if len(sheet_rows) < 2:
                    continue
                if header_global is None:
                    header_global = ["Curso"] + list(sheet_rows[0])
                    filas.append(header_global)
                for r in sheet_rows[1:]:
                    filas.append([str(sheet_name).strip()] + list(r))
        else:
            sheet = wb.active
            for row in sheet.iter_rows(values_only=True):
                if any(cell is not None and str(cell).strip() != "" for cell in row):
                    filas.append(list(row))
    elif ext == ".csv":
        if hasattr(file_obj_or_path, "read"):
            content = file_obj_or_path.read()
            if isinstance(content, bytes):
                try:
                    text = content.decode("utf-8")
                except UnicodeDecodeError:
                    text = content.decode("latin-1")
            else:
                text = content
            f = io.StringIO(text)
        else:
            f = open(file_obj_or_path, "r", encoding="utf-8", errors="replace")

        # Detectar delimitador (coma o punto y coma)
        sample = f.read(2048)
        f.seek(0)
        delimiter = ";" if sample.count(";") > sample.count(",") else ","
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if any(cell.strip() != "" for cell in row):
                filas.append(row)
        if not hasattr(file_obj_or_path, "read"):
            f.close()
    else:
        raise ValueError(f"Formato no compatible: {ext}. Utilice archivos .xlsx o .csv.")

    return filas


def procesar_archivo_dataset(file_obj_or_path, filename: str) -> Dict[str, Any]:
    """Analiza un archivo de datos (ej. ICFES, Evaluar para Avanzar, sábana SERC, caracterización),
    detecta columnas, métricas numéricas y crea agregaciones comparativas."""
    filas = leer_filas_archivo(file_obj_or_path, filename)
    if not filas or len(filas) < 2:
        return {
            "error": "El archivo no contiene suficientes filas de datos (mínimo cabecera y una fila)."
        }

    raw_headers = [str(c).strip() if c is not None else f"Columna_{i+1}" for i, c in enumerate(filas[0])]
    headers = []
    seen = {}
    for i, h in enumerate(raw_headers):
        clean_h = h or f"Columna_{i+1}"
        if clean_h in seen:
            seen[clean_h] += 1
            clean_h = f"{clean_h}_{seen[clean_h]}"
        else:
            seen[clean_h] = 1
        headers.append(clean_h)

    data_rows = filas[1:]

    # Clasificar tipos de columna
    col_values = {h: [] for h in headers}
    for row in data_rows:
        for idx, h in enumerate(headers):
            val = row[idx] if idx < len(row) else None
            col_values[h].append(val)

    numeric_cols = []
    temporal_col = None
    group_col_fallback = None
    categorical_cols = []

    _IGNORAR_COMO_METRICA = {
        "no", "no.", "n°", "nro", "id", "documento", "identificacion", "identificación",
        "cedula", "cédula", "ti", "codigo", "código", "telefono", "teléfono", "celular"
    }

    for h, vals in col_values.items():
        h_norm = h.lower().strip()
        # Detección de columna temporal (Año, Período, Cohorte, Fecha)
        if any(term in h_norm for term in ["anio", "año", "periodo", "período", "cohorte", "vigencia", "fecha"]):
            if temporal_col is None:
                temporal_col = h
                continue

        if any(term == h_norm or term in h_norm for term in ["curso", "grado", "grupo", "salon", "salón", "sede"]):
            if group_col_fallback is None:
                group_col_fallback = h
            categorical_cols.append(h)
            continue

        if h_norm in _IGNORAR_COMO_METRICA or any(h_norm.startswith(ig + " ") for ig in _IGNORAR_COMO_METRICA):
            categorical_cols.append(h)
            continue

        # Probar si es numérica o escala cualitativa SERC
        num_count = 0
        total_non_empty = 0
        for v in vals:
            if v is not None and str(v).strip() != "":
                total_non_empty += 1
                if _limpiar_numero(v) is not None:
                    num_count += 1

        if total_non_empty > 0 and (num_count / total_non_empty) >= 0.7:
            first_valid = next((_limpiar_numero(v) for v in vals if _limpiar_numero(v) is not None), None)
            if temporal_col is None and first_valid and 2018 <= first_valid <= 2030 and "puntaje" not in h_norm:
                temporal_col = h
            else:
                numeric_cols.append(h)
        else:
            categorical_cols.append(h)

    # Si no se detectó columna temporal por nombre, buscar si alguna columna numérica tiene valores de 4 dígitos (año)
    if temporal_col is None:
        for nc in list(numeric_cols):
            sample_nums = [_limpiar_numero(v) for v in col_values[nc] if _limpiar_numero(v) is not None]
            if sample_nums and all(2015 <= n <= 2030 for n in sample_nums[:10]):
                temporal_col = nc
                numeric_cols.remove(nc)
                break

    # Si sigue sin haber columna temporal, usar Curso/Grado como eje comparativo para graficar
    if temporal_col is None and group_col_fallback is not None:
        temporal_col = group_col_fallback

    # Construir comparativa por eje (temporal o por curso/cohorte)
    comparativa_temporal = {}
    if temporal_col and numeric_cols:
        grupos = defaultdict(lambda: {nc: [] for nc in numeric_cols})
        conteo_por_grupo = defaultdict(int)
        temp_idx = headers.index(temporal_col)

        for row in data_rows:
            temp_val = row[temp_idx] if temp_idx < len(row) else None
            if temp_val is None or str(temp_val).strip() == "":
                continue
            num_t = _limpiar_numero(temp_val)
            t_key = str(int(num_t)) if num_t is not None and num_t.is_integer() else str(temp_val).strip()
            conteo_por_grupo[t_key] += 1

            for nc in numeric_cols:
                nc_idx = headers.index(nc)
                val = row[nc_idx] if nc_idx < len(row) else None
                num_v = _limpiar_numero(val)
                if num_v is not None:
                    grupos[t_key][nc].append(num_v)

        keys_ordenadas = sorted(grupos.keys(), key=lambda x: (_limpiar_numero(x) is None, _limpiar_numero(x) or x))
        for t_key in keys_ordenadas:
            metricas_grupo = {}
            for nc in numeric_cols:
                vals_nc = grupos[t_key][nc]
                if vals_nc:
                    prom = round(sum(vals_nc) / len(vals_nc), 1)
                    metricas_grupo[nc] = {
                        "promedio": prom,
                        "minimo": round(min(vals_nc), 1),
                        "maximo": round(max(vals_nc), 1),
                        "total_evaluados": len(vals_nc),
                    }
                else:
                    metricas_grupo[nc] = None
            comparativa_temporal[t_key] = {
                "conteo_registros": conteo_por_grupo[t_key],
                "metricas": metricas_grupo,
            }
    elif numeric_cols:
        # Si el archivo no tiene ni año ni curso, crear cohorte general única para que siempre grafique el Radar y Línea
        temporal_col = "Cohorte"
        metricas_grupo = {}
        for nc in numeric_cols:
            nc_idx = headers.index(nc)
            vals_nc = [
                _limpiar_numero(r[nc_idx]) for r in data_rows
                if nc_idx < len(r) and _limpiar_numero(r[nc_idx]) is not None
            ]
            if vals_nc:
                metricas_grupo[nc] = {
                    "promedio": round(sum(vals_nc) / len(vals_nc), 1),
                    "minimo": round(min(vals_nc), 1),
                    "maximo": round(max(vals_nc), 1),
                    "total_evaluados": len(vals_nc),
                }
            else:
                metricas_grupo[nc] = None
        comparativa_temporal["General 2026"] = {
            "conteo_registros": len(data_rows),
            "metricas": metricas_grupo,
        }

    # Calcular variaciones entre el primer y último grupo/año detectado
    variaciones = []
    if comparativa_temporal and len(comparativa_temporal) >= 2:
        anios = list(comparativa_temporal.keys())
        primer_anio = anios[0]
        ultimo_anio = anios[-1]

        for nc in numeric_cols:
            m1 = comparativa_temporal[primer_anio]["metricas"].get(nc)
            m2 = comparativa_temporal[ultimo_anio]["metricas"].get(nc)
            if m1 and m2 and m1["promedio"] is not None and m2["promedio"] is not None:
                p1 = m1["promedio"]
                p2 = m2["promedio"]
                delta = round(p2 - p1, 1)
                pct = round(((p2 - p1) / (p1 or 1)) * 100, 1)
                variaciones.append({
                    "metrica": nc,
                    "base_anio": primer_anio,
                    "base_valor": p1,
                    "actual_anio": ultimo_anio,
                    "actual_valor": p2,
                    "delta": delta,
                    "pct": pct,
                    "tendencia": "subio" if delta > 0 else ("bajo" if delta < 0 else "igual"),
                })

    # Muestra de filas para previsualización (máximo 15)
    muestra = []
    for r in data_rows[:15]:
        cells = [str(r[idx]) if idx < len(r) and r[idx] is not None else "" for idx in range(len(headers))]
        muestra.append(cells)

    return {
        "total_filas": len(data_rows),
        "headers": headers,
        "columna_temporal": temporal_col,
        "columnas_numericas": numeric_cols,
        "columnas_categoricas": categorical_cols,
        "comparativa_temporal": comparativa_temporal,
        "variaciones": variaciones,
        "muestra_filas": muestra,
    }


def generar_diagnostico_dataset_ia(dataset) -> str:
    """Invoca el modelo Qwen 3.8 27B en Groq para generar un diagnóstico
    analítico profundo y completo sobre la información estructurada del dataset."""
    datos = dataset.datos_normalizados or {}
    titulo = dataset.titulo
    categoria = dataset.get_categoria_display()
    total_filas = datos.get("total_filas", 0)
    col_temp = datos.get("columna_temporal")
    comp = datos.get("comparativa_temporal", {})
    vars_list = datos.get("variaciones", [])

    # Construir síntesis cuantitativa para el prompt
    resumen_lineas = [
        f"Dataset: {titulo}",
        f"Categoría: {categoria} | Total de registros analizados: {total_filas}",
    ]
    if col_temp and comp:
        resumen_lineas.append(f"Eje de agrupación ({col_temp}): {', '.join(list(comp.keys())[:16])}")
        for t_k, info in list(comp.items())[:8]:
            proms = [f"{m}: {v['promedio']}" for m, v in info.get("metricas", {}).items() if v]
            resumen_lineas.append(f"- Grupo/Año {t_k} ({info['conteo_registros']} evaluados): {', '.join(proms[:6])}")
    if vars_list:
        resumen_lineas.append("Variaciones observadas entre extremos:")
        for v in vars_list[:8]:
            signo = "+" if v["delta"] > 0 else ""
            resumen_lineas.append(f"• {v['metrica']}: {v['base_valor']} ({v['base_anio']}) -> {v['actual_valor']} ({v['actual_anio']}) [Variación: {signo}{v['delta']} pts / {signo}{v['pct']}%]")

    datos_str = "\n".join(resumen_lineas)

    system_prompt = (
        "Eres Athena, Asesora de Inteligencia y Analítica Escolar del Colegio I.E.D. CEIS Sopó. "
        "Tu misión es analizar datasets institucionales (Pruebas ICFES Saber 11°, Evaluar para Avanzar, sábanas SERC, caracterizaciones) "
        "y emitir diagnósticos directivos rigurosos y completos para el Rector y los comités académicos.\n"
        "Reglas estrictas:\n"
        "1. Tono formal, ejecutivo, objetivo y cuantitativo.\n"
        "2. CERO EMOJIS O SÍMBOLOS INFORMALES en toda tu respuesta.\n"
        "3. Usa etiquetas HTML limpias (<p>, <strong>, <ul>, <li>) sin bloques markdown ```html.\n"
        "4. Redacta las 3 secciones completas de principio a fin, cerrando siempre todas las ideas y etiquetas HTML sin exceder 450 palabras."
    )

    user_prompt = (
        f"Analiza cuantitativamente el siguiente conjunto de datos institucional y emite un informe ejecutivo completo:\n\n"
        f"{datos_str}\n\n"
        "Estructura el informe exactamente en estas 3 secciones completas:\n"
        "1. Síntesis General de Rendimiento y Evolución\n"
        "2. Puntos Críticos y Áreas en Alerta (o fortalezas consolidadas)\n"
        "3. Recomendaciones Estratégicas para la Rectoría y Consejo Académico"
    )

    api_key = os.getenv("GROQ_API_KEY")
    if api_key:
        for model_id in ("llama-3.3-70b-versatile", "openai/gpt-oss-20b"):
            payload = {
                "model": model_id,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 2048,
                "temperature": 0.2,
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
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data_resp = json.loads(resp.read().decode("utf-8"))
                    texto = data_resp["choices"][0]["message"]["content"].strip()
                    texto = re.sub(r"<think>.*?</think>", "", texto, flags=re.DOTALL).strip()
                    texto = re.sub(r"<think>.*", "", texto, flags=re.DOTALL).strip()
                    texto = re.sub(r"^```html\s*|\s*```$", "", texto, flags=re.MULTILINE).strip()
                    if len(texto) > 80:
                        return texto
            except Exception:
                continue

    # Fallback analítico determinista si no hay conexión a Groq
    if vars_list:
        subidas = [v["metrica"] for v in vars_list if v["delta"] > 0]
        bajadas = [v["metrica"] for v in vars_list if v["delta"] < 0]
        p_sub = f"Se evidencian avances favorables en: <strong>{', '.join(subidas)}</strong>." if subidas else "No se observan incrementos significativos."
        p_baj = f"Se registran alertas y retrocesos prioritarios en: <strong>{', '.join(bajadas)}</strong>." if bajadas else "Todas las variables mostraron estabilidad o mejoría."
        return (
            f"<p><strong>Síntesis de Evolución Histórica:</strong> El análisis del dataset <em>{titulo}</em> sobre un total de <strong>{total_filas} registros</strong> permite contrastar el comportamiento de las cohortes evaluadas.</p>"
            f"<p><strong>Balance de Competencias:</strong> {p_sub} Por el contrario, {p_baj}</p>"
            "<p><strong>Recomendación Directiva:</strong> Se recomienda articular estos hallazgos con las comisiones de evaluación de área y focalizar los planes de nivelación con base en las brechas cuantitativas detectadas.</p>"
        )

    return (
        f"<p><strong>Diagnóstico Preliminar:</strong> Dataset <em>{titulo}</em> procesado satisfactoriamente con <strong>{total_filas} registros</strong> clasificados en la categoría <strong>{categoria}</strong>.</p>"
        "<p><strong>Directriz de Seguimiento:</strong> Los indicadores se encuentran integrados en el tablero analítico para supervisión del Consejo Académico.</p>"
    )
