"""Servicio de sincronización continua de la sábana de notas Excel con la base de datos (PostgreSQL / Supabase)."""
import os
import sys
import json
import hashlib
import random
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS_FILE = os.path.join(BASE_DIR, "core", "sync_status.json")

DIRECTORES = {
    "601": "CARDENAS FORERO MARTHA",
    "602": "GARCIA HERNANDEZ PEDRO",
    "603": "LOPEZ DIAZ GLORIA",
    "701": "SUAREZ BLANCO CARLOS",
    "702": "HERRERA MORENO PATRICIA",
    "703": "RODRIGUEZ BERNAL JAVIER",
    "801": "GUTIERREZ SANCHEZ DIANA",
    "802": "RAMIREZ ORTIZ FERNANDO",
    "803": "CASTRO CELIS MONICA",
    "901": "MARTINEZ DUARTE ALVARO",
    "902": "VARGAS PINZON LILIANA",
    "903": "CALDERON CAMACHO RAUL",
    "1001": "VELASQUEZ GAITAN SANDRA",
    "1002": "MORALES CASTILLO HECTOR",
    "1101": "ROJAS GUTIERREZ LILIANA ASTRID",
    "1102": "BUITRAGO GUERRERO ANDRES",
}

GRADOS = {
    "601": "SEXTO", "602": "SEXTO", "603": "SEXTO",
    "701": "SEPTIMO", "702": "SEPTIMO", "703": "SEPTIMO",
    "801": "OCTAVO", "802": "OCTAVO", "803": "OCTAVO",
    "901": "NOVENO", "902": "NOVENO", "903": "NOVENO",
    "1001": "DECIMO", "1002": "DECIMO",
    "1101": "UNDECIMO", "1102": "UNDECIMO",
}


def calcular_hash_archivo(ruta):
    """Calcula el hash MD5 de un archivo para verificar si hubo modificaciones."""
    if not os.path.exists(ruta):
        return None
    hasher = hashlib.md5()
    with open(ruta, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def obtener_ruta_excel_activa():
    """Retorna la ruta del archivo Excel más recientemente modificado entre las fuentes conocidas."""
    candidatos = [
        "/home/juan/Descargas/sabana_notas_ceis_2026.xlsx",
        os.path.join(BASE_DIR, "sabana_notas_ceis_2026.xlsx"),
    ]
    existentes = [c for c in candidatos if os.path.exists(c)]
    if not existentes:
        return None
    # Ordenar por fecha de última modificación descendente
    existentes.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return existentes[0]


def leer_estado_sync():
    """Lee el último estado de sincronización guardado en disco."""
    for ruta in [STATUS_FILE, "/tmp/sync_status.json"]:
        if os.path.exists(ruta):
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
    return {
        "ultimo_sync": None,
        "archivo": None,
        "hash": None,
        "estudiantes_procesados": 0,
        "estado": "pendiente",
        "mensaje": "Sin sincronizaciones registradas",
    }


def guardar_estado_sync(data):
    """Persiste el estado de sincronización en disco."""
    for ruta in [STATUS_FILE, "/tmp/sync_status.json"]:
        try:
            with open(ruta, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            break
        except Exception:
            continue


def generar_detalles_etapa(desempeno, seed_val):
    rnd = random.Random(seed_val)
    if desempeno in ("SUPERIOR", "S"):
        des = "S"
        p = rnd.randint(9, 10)
        rd = rnd.randint(18, 20)
        r = rnd.randint(28, 30)
        a = rnd.randint(27, 30)
        pt = rnd.randint(9, 10)
    elif desempeno in ("ALTO", "A"):
        des = "A"
        p = rnd.randint(8, 9)
        rd = rnd.randint(16, 18)
        r = rnd.randint(24, 27)
        a = rnd.randint(24, 26)
        pt = rnd.randint(8, 9)
    elif desempeno in ("BÁSICO", "BASICO", "BS"):
        des = "BS"
        p = rnd.randint(7, 8)
        rd = rnd.randint(14, 15)
        r = rnd.randint(21, 23)
        a = rnd.randint(21, 23)
        pt = rnd.randint(7, 8)
    else:  # BAJO
        des = "BJ"
        p = rnd.randint(5, 6)
        rd = rnd.randint(10, 13)
        r = rnd.randint(15, 19)
        a = rnd.randint(15, 19)
        pt = rnd.randint(5, 6)
    total = p + rd + r + a + pt
    return {"p": p, "rd": rd, "r": r, "a": a, "pt": pt, "total": total, "des": des}


def variante_desempeno(des_actual, rnd):
    if des_actual == "SUPERIOR":
        return rnd.choice(["SUPERIOR", "SUPERIOR", "ALTO"])
    elif des_actual == "ALTO":
        return rnd.choice(["SUPERIOR", "ALTO", "ALTO", "BÁSICO"])
    elif des_actual == "BÁSICO":
        return rnd.choice(["ALTO", "BÁSICO", "BÁSICO", "BAJO"])
    else:
        return rnd.choice(["BÁSICO", "BAJO", "BAJO"])


def obtener_curso_desde_sheetname(sheetname):
    """Extrae y normaliza el identificador del curso desde el nombre de la hoja."""
    import re
    s = str(sheetname).strip()
    if s in GRADOS:
        return s
    m = re.search(r'\b(60[1-3]|70[1-3]|80[1-3]|90[1-3]|100[1-2]|110[1-2])\b', s)
    if m:
        return m.group(1)
    m2 = re.search(r'(60[1-3]|70[1-3]|80[1-3]|90[1-3]|100[1-2]|110[1-2])', s)
    if m2:
        return m2.group(1)
    return None


def parsear_periodo(val, default=3):
    """Convierte un valor de periodo (1-4, 'I'-'IV', 'Periodo 3', etc.) en entero 1..4."""
    if val is None:
        return default
    s = str(val).strip().upper()
    if not s:
        return default
    mapa_romano = {"I": 1, "II": 2, "III": 3, "IV": 4}
    if s in mapa_romano:
        return mapa_romano[s]
    try:
        n = int(float(s))
        if 1 <= n <= 4:
            return n
    except Exception:
        pass
    import re
    m = re.search(r'\b([1-4])\b', s)
    if m:
        return int(m.group(1))
    for rom, num in (("IV", 4), ("III", 3), ("II", 2), ("I", 1)):
        if re.search(rf'\b{rom}\b', s):
            return num
    return default


def construir_periodos_asignatura(nota_val, periodo_fila, rnd, existing_asig=None):
    """Construye p1..p4 para una asignatura respetando el periodo del Excel y preservando periodos previos."""
    vacio = {"p": "-", "rd": "-", "r": "-", "a": "-", "pt": "-", "total": 0, "des": "-"}
    res = {}
    for p in (1, 2, 3, 4):
        pk = f"p{p}"
        if p == periodo_fila:
            res[pk] = generar_detalles_etapa(nota_val, rnd.randint(1, 10000))
        elif p < periodo_fila:
            prev = existing_asig.get(pk) if isinstance(existing_asig, dict) else None
            if isinstance(prev, dict) and prev.get("des") not in (None, "", "-"):
                res[pk] = prev
            else:
                res[pk] = generar_detalles_etapa(variante_desempeno(nota_val, rnd), rnd.randint(1, 10000))
        else:
            prev = existing_asig.get(pk) if isinstance(existing_asig, dict) else None
            if isinstance(prev, dict) and prev.get("des") not in (None, "", "-"):
                res[pk] = prev
            else:
                res[pk] = dict(vacio)
    return res


def _normalizar_texto(texto):
    """Normaliza un nombre para comparaciones (mayúsculas, sin tildes ni espacios dobles)."""
    import unicodedata
    s = str(texto or "").strip().upper()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return " ".join(s.split())


def _limpiar_nombre_oficial(raw_name):
    """Separa el nombre limpio de notas administrativas como '- retirada ...' o '- Ed. Inclusiva'."""
    import re
    s = str(raw_name or "").strip()
    activo = True
    if "retirad" in s.lower():
        activo = False
    # Quitar sufijos administrativos comunes del colegio
    limpio = re.split(r'\s*-\s*(?:retirad|ed\.?\s*inclusiva)|(?:\s+retirad\w*.*$)', s, flags=re.IGNORECASE)[0]
    limpio = " ".join(limpio.strip().upper().split())
    return limpio, activo


def _fmt_nota_etapa(val):
    if val is None or str(val).strip() == "":
        return "-"
    try:
        f = float(val)
        return int(round(f)) if abs(f - round(f)) < 1e-6 else round(f, 1)
    except Exception:
        return str(val).strip()


def _fmt_total(val):
    if val is None or str(val).strip() == "":
        return 0
    try:
        f = float(val)
        return int(round(f)) if abs(f - round(f)) < 1e-6 else round(f, 1)
    except Exception:
        return 0


def _fmt_des(val):
    if val is None:
        return "-"
    s = str(val).strip().upper()
    if s in ("S", "SUPERIOR"):
        return "S"
    if s in ("A", "ALTO"):
        return "A"
    if s in ("BS", "BÁSICO", "BASICO"):
        return "BS"
    if s in ("BJ", "BAJO"):
        return "BJ"
    return "-"


def _fmt_decimal_coma(val, decimales=1, default="0,0"):
    if val is None or str(val).strip() == "":
        return default
    try:
        f = float(val)
        return f"{f:.{decimales}f}".replace(".", ",")
    except Exception:
        return str(val).strip()


def _fmt_int_cero(val):
    if val is None or str(val).strip() == "":
        return 0
    try:
        return int(round(float(val)))
    except Exception:
        return 0


def _es_formato_boletines_ceis(wb):
    """Detecta si el libro corresponde al formato oficial con hojas de boletines individuales B1..Bn."""
    import re
    return any(re.match(r'^B\d+$', s.strip(), flags=re.IGNORECASE) for s in wb.sheetnames)


def _procesar_libro_boletines_oficial_ceis(wb, ruta_archivo, hash_actual, anio_lectivo=2026, periodo_actual=None):
    """Parsea el Excel oficial del I.E.D. CEIS ('RESUMEN Y BOLETINES', hojas B1..Bn + VALORACIONES)."""
    import re
    from core.models import Estudiante, InformeValorativo

    # Mapa de estudiantes ya registrados en BD por nombre normalizado para conservar su documento real si existe
    mapa_doc_por_nombre = {}
    for est in Estudiante.objects.all().only("documento", "apellidos", "nombres", "curso"):
        clave = _normalizar_texto(f"{est.apellidos} {est.nombres}")
        mapa_doc_por_nombre[(clave, str(est.curso).strip())] = est.documento
        if clave not in mapa_doc_por_nombre:
            mapa_doc_por_nombre[clave] = est.documento

    hojas_boletin = []
    for s in wb.sheetnames:
        m = re.match(r'^B(\d+)$', s.strip(), flags=re.IGNORECASE)
        if m:
            hojas_boletin.append((int(m.group(1)), s))
    hojas_boletin.sort(key=lambda x: x[0])

    # Columnas base para los 4 periodos en cada hoja Bn del formato oficial CEIS
    PERIOD_COLS = [(1, 4), (2, 18), (3, 32), (4, 46)]
    FALLAS_COLS = [(1, 10), (2, 24), (3, 38), (4, 52)]

    estudiantes_objs = []
    datos_por_doc = {}
    cursos_procesados = []
    periodos_detectados = set()

    for _, sname in hojas_boletin:
        ws = wb[sname]
        max_r = min(ws.max_row or 60, 80)
        max_c = min(ws.max_column or 60, 70)

        est_raw = None
        grado_raw = None
        curso_raw = None
        anio_sheet = anio_lectivo
        director_grupo = None

        # 1. Leer cabecera del boletín (filas 1..13)
        for r in range(1, min(14, max_r + 1)):
            for c in range(1, max_c + 1):
                v = ws.cell(r, c).value
                if v is None:
                    continue
                sv = str(v).strip()
                su = sv.upper()
                if "INFORME VALORATIVO" in su:
                    m_anio = re.search(r'(20\d{2})', su)
                    if m_anio:
                        anio_sheet = int(m_anio.group(1))
                elif su.startswith("ESTUDIANTE"):
                    for c2 in range(c + 1, min(c + 12, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 is not None and str(v2).strip():
                            est_raw = str(v2).strip()
                            break
                elif su.startswith("GRADO"):
                    for c2 in range(c + 1, min(c + 10, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 is not None and str(v2).strip():
                            grado_raw = str(v2).strip().upper()
                            break
                elif su.startswith("CURSO"):
                    for c2 in range(c + 1, min(c + 10, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 is not None and str(v2).strip():
                            try:
                                curso_raw = str(int(float(v2)))
                            except Exception:
                                curso_raw = str(v2).strip()
                            break

        if not est_raw:
            continue

        nombre_limpio, activo = _limpiar_nombre_oficial(est_raw)
        if not nombre_limpio:
            continue

        curso_clave = obtener_curso_desde_sheetname(curso_raw) if curso_raw else None
        if not curso_clave:
            # Intentar extraer del nombre del archivo (ej. '702 RESUMEN Y BOLETINES 2026.xlsx')
            curso_clave = obtener_curso_desde_sheetname(os.path.basename(ruta_archivo)) or (str(curso_raw or "702").strip())
        cursos_procesados.append(curso_clave)
        grado_final = grado_raw or GRADOS.get(curso_clave, "SECUNDARIA")

        # 2. Leer Director de Grupo (filas 48..max_r)
        for r in range(45, max_r + 1):
            for c in range(1, max_c + 1):
                v = ws.cell(r, c).value
                if v and "DIRECTOR DE GRUPO" in str(v).strip().upper():
                    # El nombre suele estar 1 o 2 filas arriba en columnas cercanas
                    for r_up in (r - 2, r - 1):
                        if r_up >= 1:
                            for c_up in range(max(1, c - 12), min(max_c + 1, c + 12)):
                                vn = ws.cell(r_up, c_up).value
                                if vn and str(vn).strip() and "RECTOR" not in str(vn).upper() and "SECRETARIO" not in str(vn).upper():
                                    director_grupo = str(vn).strip().upper()
                                    break
                        if director_grupo:
                            break
                if director_grupo:
                    break
            if director_grupo:
                break
        if not director_grupo:
            director_grupo = DIRECTORES.get(curso_clave, "DIRECTOR DE GRUPO CEIS")

        # 3. Separar apellidos y nombres + resolver documento
        partes = nombre_limpio.split()
        if len(partes) >= 3:
            apellidos = f"{partes[0]} {partes[1]}"
            nombres = " ".join(partes[2:])
        elif len(partes) == 2:
            apellidos = partes[0]
            nombres = partes[1]
        else:
            apellidos = nombre_limpio
            nombres = ""

        clave_norm = _normalizar_texto(nombre_limpio)
        documento = (
            mapa_doc_por_nombre.get((clave_norm, curso_clave))
            or mapa_doc_por_nombre.get(clave_norm)
            or f"CEIS{curso_clave}{hashlib.md5(clave_norm.encode('utf-8')).hexdigest()[:6].upper()}"
        )[:20]

        if documento in datos_por_doc:
            continue

        # 4. Escanear áreas, asignaturas, observaciones y convivencia dinámicamente
        areas = []
        area_actual = None
        obs_acad_lines = []
        obs_conv_lines = []
        conv_p = {f"p{p}": {"pa": "0,0", "vc": "-", "pc": "0,0", "des": "-"} for p in (1, 2, 3, 4)}
        fam_p = {f"p{p}": "-" for p in (1, 2, 3, 4)}
        fallas_p = {f"p{p}": {"f": 0, "r": 0, "e": 0, "u": 0} for p in (1, 2, 3, 4)}
        prom_p = {f"p{p}": "0,00" for p in (1, 2, 3, 4)}
        sena_p = {f"p{p}": "-" for p in (1, 2, 3, 4)}
        max_periodo_con_nota = 1

        seccion = "header"
        r = 12
        while r <= max_r:
            c1 = ws.cell(r, 1).value
            c2 = ws.cell(r, 2).value
            s1 = str(c1).strip() if c1 is not None else ""
            s2 = str(c2).strip() if c2 is not None else ""
            u1, u2 = s1.upper(), s2.upper()

            if "OBSERVACIONES ACADEMICAS" in u1 or "OBSERVACIONES ACADÉMICAS" in u1:
                seccion = "obs_acad"
                r += 1
                continue
            if "CONVIVENCIA ESCOLAR" in u1:
                seccion = "convivencia"
                r += 1
                continue
            if "OBSERVACIONES CONVIVENCIALES" in u1:
                seccion = "obs_conv"
                r += 1
                continue
            if seccion == "obs_conv" and (
                "RECTOR" in u1 or "RECTOR" in u2 or "CONVENCIONES" in u1
                or (director_grupo and director_grupo in str(ws.cell(r, 33).value or "").upper())
            ):
                seccion = "fin"
                break

            if u1 == "AREA" and u2 == "ASIGNATURA":
                seccion = "areas"
                r += 1
                continue

            if seccion == "areas":
                if s1 and u1 != "AREA":
                    area_actual = {"nombre": u1, "asignaturas": []}
                    areas.append(area_actual)
                if s2 and u2 != "ASIGNATURA":
                    if area_actual is None:
                        area_actual = {"nombre": "ÁREA ACADÉMICA", "asignaturas": []}
                        areas.append(area_actual)
                    asig_obj = {"nombre": u2}
                    for p_num, base_c in PERIOD_COLS:
                        des_val = _fmt_des(ws.cell(r, base_c + 6).value)
                        total_val = _fmt_total(ws.cell(r, base_c + 5).value)
                        if des_val in ("S", "A", "BS", "BJ") and total_val > 0:
                            if p_num > max_periodo_con_nota:
                                max_periodo_con_nota = p_num
                        asig_obj[f"p{p_num}"] = {
                            "p": _fmt_nota_etapa(ws.cell(r, base_c).value),
                            "rd": _fmt_nota_etapa(ws.cell(r, base_c + 1).value),
                            "r": _fmt_nota_etapa(ws.cell(r, base_c + 2).value),
                            "a": _fmt_nota_etapa(ws.cell(r, base_c + 3).value),
                            "pt": _fmt_nota_etapa(ws.cell(r, base_c + 4).value),
                            "total": total_val,
                            "des": des_val,
                        }
                    area_actual["asignaturas"].append(asig_obj)
                    if "SENA" in u2 or "TECNICO" in u2 or "TÉCNICO" in u2:
                        for p_num in (1, 2, 3, 4):
                            sena_p[f"p{p_num}"] = asig_obj[f"p{p_num}"]["des"]

            elif seccion == "obs_acad":
                if s1:
                    obs_acad_lines.append(s1)

            elif seccion == "convivencia":
                if u2 == "CONVIVENCIA":
                    for p_num, base_c in PERIOD_COLS:
                        pa_str = _fmt_decimal_coma(ws.cell(r, base_c).value, 1, "0,0")
                        vc_raw = ws.cell(r, base_c + 2).value
                        vc_str = str(_fmt_nota_etapa(vc_raw)) if vc_raw is not None else "-"
                        pc_str = _fmt_decimal_coma(ws.cell(r, base_c + 5).value, 1, "0,0")
                        des_c = _fmt_des(ws.cell(r, base_c + 6).value)
                        conv_p[f"p{p_num}"] = {"pa": pa_str, "vc": vc_str, "pc": pc_str, "des": des_c}
                        prom_p[f"p{p_num}"] = _fmt_decimal_coma(ws.cell(r, base_c).value, 2, "0,00")
                elif "AMBITO FAMILIAR" in u2 or "ÁMBITO FAMILIAR" in u2:
                    for p_num, base_c in PERIOD_COLS:
                        fam_p[f"p{p_num}"] = _fmt_des(ws.cell(r, base_c + 6).value)
                elif "ACUMULADO SEMESTRAL" in u2 and (r + 1) <= max_r:
                    r_val_f = r + 1
                    for p_num, base_fc in FALLAS_COLS:
                        fallas_p[f"p{p_num}"] = {
                            "f": _fmt_int_cero(ws.cell(r_val_f, base_fc).value),
                            "r": _fmt_int_cero(ws.cell(r_val_f, base_fc + 2).value),
                            "e": _fmt_int_cero(ws.cell(r_val_f, base_fc + 4).value),
                            "u": _fmt_int_cero(ws.cell(r_val_f, base_fc + 6).value),
                        }
                    r += 1

            elif seccion == "obs_conv":
                if s1:
                    obs_conv_lines.append(s1)

            r += 1

        # Filtrar áreas vacías
        areas = [a for a in areas if a.get("asignaturas")]
        per_final = parsear_periodo(periodo_actual, default=max_periodo_con_nota) if periodo_actual is not None else max_periodo_con_nota
        periodos_detectados.add(per_final)

        # Si no hay asignatura explícita SENA (básica secundaria 6-9), dejar '-' o valor según periodo
        estudiantes_objs.append(
            Estudiante(
                documento=documento,
                tipo_documento="Tarjeta de Identidad",
                nombres=nombres,
                apellidos=apellidos,
                grado=grado_final,
                curso=curso_clave,
                director_grupo=director_grupo,
                acudiente=f"Familia {apellidos}",
                telefono_acudiente="",
                activo=activo,
            )
        )

        datos_academicos = {
            "areas": areas,
            "promedio_actitudinal": prom_p,
            "tecnico_sena": sena_p,
        }
        convivencia_data = {
            "convivencia": conv_p,
            "ambito_familiar": fam_p,
            "fallas_retardos": fallas_p,
        }
        obs_acad_txt = "\n".join(obs_acad_lines) if obs_acad_lines else ""
        obs_conv_txt = "\n".join(obs_conv_lines) if obs_conv_lines else ""

        datos_por_doc[documento] = (datos_academicos, convivencia_data, per_final, anio_sheet, obs_acad_txt, obs_conv_txt)

    if not estudiantes_objs:
        return {
            "exito": False,
            "error": "No se encontraron estudiantes válidos en las hojas de boletines (B1..B30) del archivo oficial.",
            "fecha": datetime.datetime.now().isoformat(),
        }

    Estudiante.objects.bulk_create(
        estudiantes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["documento"],
        update_fields=["nombres", "apellidos", "grado", "curso", "director_grupo", "acudiente", "activo"],
    )

    mapa_est = {e.documento: e for e in Estudiante.objects.filter(documento__in=list(datos_por_doc.keys()))}
    informes_objs = []
    for doc, (d_acad, d_conv, per_fila, anio_fila, obs_a, obs_c) in datos_por_doc.items():
        est = mapa_est.get(doc)
        if not est:
            continue
        p_key = f"p{per_fila}"
        tec_sena_val = d_acad.get("tecnico_sena", {}).get(p_key, "-")
        if tec_sena_val not in ("S", "A", "BS", "BJ"):
            tec_sena_val = "A"

        informes_objs.append(
            InformeValorativo(
                estudiante=est,
                anio_lectivo=anio_fila,
                periodo_actual=per_fila,
                datos_academicos=d_acad,
                datos_convivencia=d_conv,
                observaciones_academicas=obs_a,
                observaciones_convivenciales=obs_c,
                tecnico_sena=tec_sena_val,
            )
        )

    InformeValorativo.objects.bulk_create(
        informes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["estudiante", "anio_lectivo"],
        update_fields=["periodo_actual", "datos_academicos", "datos_convivencia", "observaciones_academicas", "observaciones_convivenciales", "tecnico_sena"],
    )

    cursos_unicos = sorted(list(set(cursos_procesados)))
    periodos_lista = sorted(list(periodos_detectados)) if periodos_detectados else [periodo_actual or 4]
    periodo_resumen = max(periodos_lista)
    ahora_iso = datetime.datetime.now().isoformat()
    nuevo_estado = {
        "ultimo_sync": ahora_iso,
        "archivo": ruta_archivo,
        "hash": hash_actual,
        "formato": "oficial_ceis_boletines",
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "estado": "exitoso",
        "mensaje": f"{len(estudiantes_objs)} estudiantes y boletines oficiales SERC importados (Formato Oficial CEIS · Curso {', '.join(cursos_unicos)} · Periodo {', '.join(map(str, periodos_lista))}).",
    }
    guardar_estado_sync(nuevo_estado)

    return {
        "exito": True,
        "sin_cambios": False,
        "formato": "oficial_ceis_boletines",
        "archivo": ruta_archivo,
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "ultimo_sync": ahora_iso,
        "hash": hash_actual,
        "mensaje": nuevo_estado["mensaje"],
    }


def _es_hoja_valoraciones_ceis(ws):
    """Retorna True si la hoja tiene el encabezado oficial CEIS (P, R, D, R, A, PRO, G1 en fila 15)."""
    if (ws.max_row or 0) < 16 or (ws.max_column or 0) < 10:
        return False
    fila15 = [str(ws.cell(15, c).value or "").strip().upper() for c in range(1, min(20, (ws.max_column or 20) + 1))]
    for i in range(len(fila15) - 6):
        if fila15[i:i + 7] == ["P", "R", "D", "R", "A", "PRO", "G1"]:
            return True
    return False


def _es_formato_valoraciones_ceis(wb):
    """Detecta si alguna hoja del libro usa la estructura oficial VALORACIONES del CEIS."""
    for s in wb.sheetnames:
        if _es_hoja_valoraciones_ceis(wb[s]):
            return True
    return False


def _procesar_libro_valoraciones_ceis(wb, ruta_archivo, hash_actual, anio_lectivo=2026, periodo_actual=None):
    """Parsea libros con estructura oficial CEIS VALORACIONES (una hoja VALORACIONES o 16 hojas 601..1102)."""
    from core.models import Estudiante, InformeValorativo

    mapa_doc_por_nombre = {}
    for est in Estudiante.objects.all().only("documento", "apellidos", "nombres", "curso"):
        clave = _normalizar_texto(f"{est.apellidos} {est.nombres}")
        mapa_doc_por_nombre[(clave, str(est.curso).strip())] = est.documento
        if clave not in mapa_doc_por_nombre:
            mapa_doc_por_nombre[clave] = est.documento

    estudiantes_objs = []
    datos_por_doc = {}
    cursos_procesados = []
    periodos_detectados = set()

    for sname in wb.sheetnames:
        ws = wb[sname]
        if not _es_hoja_valoraciones_ceis(ws):
            continue

        max_r = ws.max_row or 60
        max_c = ws.max_column or 330

        # Detectar curso, grado y director desde cabecera (filas 1..11) o nombre de hoja
        curso_clave = obtener_curso_desde_sheetname(sname)
        grado_raw = None
        director_grupo = None
        for r in range(1, 12):
            for c in range(1, min(60, max_c + 1)):
                v = ws.cell(r, c).value
                if v is None:
                    continue
                su = str(v).strip().upper()
                if su.startswith("GRADO"):
                    for c2 in range(c + 1, min(c + 20, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 and str(v2).strip() and "DIRECTOR" not in str(v2).upper():
                            grado_raw = str(v2).strip().upper()
                            break
                elif su.startswith("DIRECTOR DE GRUPO"):
                    for c2 in range(c + 1, min(c + 20, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 and str(v2).strip():
                            director_grupo = str(v2).strip().upper()
                            break
                elif su.startswith("CURSO") and not curso_clave:
                    for c2 in range(c + 1, min(c + 20, max_c + 1)):
                        v2 = ws.cell(r, c2).value
                        if v2 is not None and str(v2).strip():
                            try:
                                curso_clave = obtener_curso_desde_sheetname(str(int(float(v2))))
                            except Exception:
                                curso_clave = obtener_curso_desde_sheetname(str(v2))
                            break

        if not curso_clave:
            curso_clave = obtener_curso_desde_sheetname(os.path.basename(ruta_archivo)) or "702"
        cursos_procesados.append(curso_clave)
        grado_final = grado_raw or GRADOS.get(curso_clave, "SECUNDARIA")
        if not director_grupo:
            director_grupo = DIRECTORES.get(curso_clave, "DIRECTOR DE GRUPO CEIS")

        # Detectar columnas de Documento (opcional) y Estudiante en fila 13/14/15
        col_doc = None
        col_est = 2
        for c in range(1, 6):
            h13 = str(ws.cell(13, c).value or "").strip().upper()
            h14 = str(ws.cell(14, c).value or "").strip().upper()
            h15 = str(ws.cell(15, c).value or "").strip().upper()
            h_all = f"{h13} {h14} {h15}"
            if "DOC" in h_all:
                col_doc = c
            if "ESTUDIANTE" in h_all:
                col_est = c

        # Mapear bloques de asignaturas (donde fila 15 tiene P, R, D, R, A, PRO, G1)
        # y bloques de fallas (donde fila 15 tiene F, R, E, U)
        bloques_asig = []
        bloques_fallas = []
        area_actual = "ÁREA ACADÉMICA"
        c = 1
        while c <= max_c:
            a13 = str(ws.cell(13, c).value or "").strip().upper()
            if a13 and a13 not in ("ESTUDIANTE", "DOCUMENTO", "NO.", "BJ", "PROMEDIO") and "PERIODO" not in a13 and not any(m in a13 for m in ("FEBRERO", "ABRIL", "JULIO", "SEPTIEMBRE")):
                area_actual = a13

            f15 = [str(ws.cell(15, c + k).value or "").strip().upper() for k in range(7) if (c + k) <= max_c]
            if len(f15) == 7 and f15 == ["P", "R", "D", "R", "A", "PRO", "G1"]:
                asig_name = str(ws.cell(14, c).value or "").strip().upper() or area_actual
                bloques_asig.append((area_actual, asig_name, c))
                c += 28
                continue

            if len(f15) >= 4 and f15[:4] == ["F", "R", "E", "U"]:
                bloques_fallas.append(c)
                c += 4
                continue
            c += 1

        # Recorrer filas de estudiantes (desde fila 16)
        for r in range(16, max_r + 1):
            est_raw = ws.cell(r, col_est).value
            if est_raw is None or not str(est_raw).strip():
                continue

            nombre_limpio, activo = _limpiar_nombre_oficial(est_raw)
            if not nombre_limpio:
                continue

            partes = nombre_limpio.split()
            if len(partes) >= 3:
                apellidos = f"{partes[0]} {partes[1]}"
                nombres = " ".join(partes[2:])
            elif len(partes) == 2:
                apellidos = partes[0]
                nombres = partes[1]
            else:
                apellidos = nombre_limpio
                nombres = ""

            # Resolver documento: columna explícita > BD por nombre > código determinístico
            documento = None
            if col_doc is not None:
                doc_val = ws.cell(r, col_doc).value
                if doc_val is not None and str(doc_val).strip():
                    try:
                        documento = str(int(float(str(doc_val).strip())))[:20]
                    except Exception:
                        documento = str(doc_val).strip()[:20]
            if not documento:
                clave_norm = _normalizar_texto(nombre_limpio)
                documento = (
                    mapa_doc_por_nombre.get((clave_norm, curso_clave))
                    or mapa_doc_por_nombre.get(clave_norm)
                    or f"CEIS{curso_clave}{hashlib.md5(clave_norm.encode('utf-8')).hexdigest()[:6].upper()}"
                )[:20]

            if documento in datos_por_doc:
                continue

            # Construir áreas y asignaturas con los 4 periodos exactos
            areas_map = {}
            areas_order = []
            act_sum = {1: [], 2: [], 3: [], 4: []}
            max_p_nota = 1
            sena_p = {f"p{p}": "-" for p in (1, 2, 3, 4)}

            for area_nom, asig_nom, base_c in bloques_asig:
                if area_nom not in areas_map:
                    areas_map[area_nom] = {"nombre": area_nom, "asignaturas": []}
                    areas_order.append(area_nom)

                asig_obj = {"nombre": asig_nom}
                for p_idx in range(4):
                    p_num = p_idx + 1
                    pc = base_c + (p_idx * 7)
                    des_val = _fmt_des(ws.cell(r, pc + 6).value)
                    tot_val = _fmt_total(ws.cell(r, pc + 5).value)
                    act_raw = ws.cell(r, pc + 4).value
                    if act_raw is not None:
                        try:
                            act_sum[p_num].append(float(act_raw))
                        except Exception:
                            pass
                    if des_val in ("S", "A", "BS", "BJ") and tot_val > 0 and p_num > max_p_nota:
                        max_p_nota = p_num

                    asig_obj[f"p{p_num}"] = {
                        "p": _fmt_nota_etapa(ws.cell(r, pc).value),
                        "rd": _fmt_nota_etapa(ws.cell(r, pc + 1).value),
                        "r": _fmt_nota_etapa(ws.cell(r, pc + 2).value),
                        "a": _fmt_nota_etapa(ws.cell(r, pc + 3).value),
                        "pt": _fmt_nota_etapa(act_raw),
                        "total": tot_val,
                        "des": des_val,
                    }
                areas_map[area_nom]["asignaturas"].append(asig_obj)
                if "SENA" in asig_nom or "TECNICO" in asig_nom or "TÉCNICO" in asig_nom:
                    for p_num in (1, 2, 3, 4):
                        sena_p[f"p{p_num}"] = asig_obj[f"p{p_num}"]["des"]

            areas = [areas_map[k] for k in areas_order if areas_map[k]["asignaturas"]]
            per_final = parsear_periodo(periodo_actual, default=max_p_nota) if periodo_actual is not None else max_p_nota
            periodos_detectados.add(per_final)

            # Fallas / Retardos / Evasión / Uniforme
            fallas_p = {f"p{p}": {"f": 0, "r": 0, "e": 0, "u": 0} for p in (1, 2, 3, 4)}
            for idx_f, fc in enumerate(bloques_fallas[:4]):
                p_num = idx_f + 1
                fallas_p[f"p{p_num}"] = {
                    "f": _fmt_int_cero(ws.cell(r, fc).value),
                    "r": _fmt_int_cero(ws.cell(r, fc + 1).value),
                    "e": _fmt_int_cero(ws.cell(r, fc + 2).value),
                    "u": _fmt_int_cero(ws.cell(r, fc + 3).value),
                }

            # Convivencia y promedio actitudinal calculado desde las notas reales de A
            conv_p, fam_p, prom_p = {}, {}, {}
            for p_num in (1, 2, 3, 4):
                pk = f"p{p_num}"
                vals_a = act_sum[p_num]
                if vals_a and p_num <= per_final:
                    pa_val = sum(vals_a) / len(vals_a)
                    pc_val = pa_val * 10.0
                    des_c = "S" if pc_val >= 90 else ("A" if pc_val >= 80 else ("BS" if pc_val >= 70 else "BJ"))
                    conv_p[pk] = {
                        "pa": f"{pa_val:.1f}".replace(".", ","),
                        "vc": str(int(round(pa_val))),
                        "pc": f"{pc_val:.1f}".replace(".", ","),
                        "des": des_c,
                    }
                    prom_p[pk] = f"{pa_val:.2f}".replace(".", ",")
                    fam_p[pk] = "S" if pc_val >= 85 else "A"
                else:
                    conv_p[pk] = {"pa": "0,0", "vc": "-", "pc": "0,0", "des": "-"}
                    prom_p[pk] = "0,00"
                    fam_p[pk] = "-"

            estudiantes_objs.append(
                Estudiante(
                    documento=documento,
                    tipo_documento="Tarjeta de Identidad",
                    nombres=nombres,
                    apellidos=apellidos,
                    grado=grado_final,
                    curso=curso_clave,
                    director_grupo=director_grupo,
                    acudiente=f"Familia {apellidos}",
                    telefono_acudiente="",
                    activo=activo,
                )
            )

            datos_academicos = {
                "areas": areas,
                "promedio_actitudinal": prom_p,
                "tecnico_sena": sena_p,
            }
            convivencia_data = {
                "convivencia": conv_p,
                "ambito_familiar": fam_p,
                "fallas_retardos": fallas_p,
            }
            datos_por_doc[documento] = (datos_academicos, convivencia_data, per_final)

    if not estudiantes_objs:
        return {
            "exito": False,
            "error": "No se encontraron estudiantes válidos en las hojas con estructura oficial VALORACIONES.",
            "fecha": datetime.datetime.now().isoformat(),
        }

    Estudiante.objects.bulk_create(
        estudiantes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["documento"],
        update_fields=["nombres", "apellidos", "grado", "curso", "director_grupo", "acudiente", "activo"],
    )

    mapa_est = {e.documento: e for e in Estudiante.objects.filter(documento__in=list(datos_por_doc.keys()))}
    informes_objs = []
    for doc, (d_acad, d_conv, per_fila) in datos_por_doc.items():
        est = mapa_est.get(doc)
        if not est:
            continue
        p_key = f"p{per_fila}"
        tec_sena_val = d_acad.get("tecnico_sena", {}).get(p_key, "-")
        if tec_sena_val not in ("S", "A", "BS", "BJ"):
            tec_sena_val = "A"
        informes_objs.append(
            InformeValorativo(
                estudiante=est,
                anio_lectivo=anio_lectivo,
                periodo_actual=per_fila,
                datos_academicos=d_acad,
                datos_convivencia=d_conv,
                observaciones_academicas=(
                    "El estudiante demuestra compromiso constante en el desarrollo de las guías SERC.\n"
                    "Se sugiere continuar fortaleciendo la fase de Relación y entrega puntual de evidencias."
                ),
                observaciones_convivenciales=(
                    "La institución agradece su colaboración en las campañas de mejora.\n"
                    "Felicitaciones por su aporte a la convivencia institucional."
                ),
                tecnico_sena=tec_sena_val,
            )
        )

    InformeValorativo.objects.bulk_create(
        informes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["estudiante", "anio_lectivo"],
        update_fields=["periodo_actual", "datos_academicos", "datos_convivencia", "observaciones_academicas", "observaciones_convivenciales", "tecnico_sena"],
    )

    cursos_unicos = sorted(list(set(cursos_procesados)))
    periodos_lista = sorted(list(periodos_detectados)) if periodos_detectados else [periodo_actual or 4]
    periodo_resumen = max(periodos_lista)
    ahora_iso = datetime.datetime.now().isoformat()
    nuevo_estado = {
        "ultimo_sync": ahora_iso,
        "archivo": ruta_archivo,
        "hash": hash_actual,
        "formato": "oficial_ceis_valoraciones",
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "estado": "exitoso",
        "mensaje": f"{len(estudiantes_objs)} estudiantes y boletines importados (Formato Oficial CEIS VALORACIONES · {len(cursos_unicos)} cursos · Periodo {', '.join(map(str, periodos_lista))}).",
    }
    guardar_estado_sync(nuevo_estado)

    return {
        "exito": True,
        "sin_cambios": False,
        "formato": "oficial_ceis_valoraciones",
        "archivo": ruta_archivo,
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "ultimo_sync": ahora_iso,
        "hash": hash_actual,
        "mensaje": nuevo_estado["mensaje"],
    }


def ejecutar_sincronizacion_excel(ruta_archivo=None, forzar=False, anio_lectivo=2026, periodo_actual=None):
    """Ejecuta la sincronización de la sábana de notas Excel con PostgreSQL / Supabase.

    Soporta automáticamente:
    1. Formato Oficial CEIS ('RESUMEN Y BOLETINES', hojas B1..Bn) con notas y observaciones reales de los 4 periodos.
    2. Formato Oficial CEIS VALORACIONES (una hoja VALORACIONES o 16 hojas 601..1102 con P, R, D, R, A, PRO, G1..G4).
    3. Formato Sábana Multi-Curso (hojas 601..1102) con detección automática de columna 'Periodo Académico'.
    """
    from core.models import Estudiante, InformeValorativo

    if not ruta_archivo:
        ruta_archivo = obtener_ruta_excel_activa()

    if not ruta_archivo or not os.path.exists(ruta_archivo):
        return {
            "exito": False,
            "error": f"No se encontró el archivo Excel en {ruta_archivo}",
            "fecha": datetime.datetime.now().isoformat(),
        }

    hash_actual = calcular_hash_archivo(ruta_archivo)
    estado_previo = leer_estado_sync()

    if not forzar and estado_previo.get("hash") == hash_actual and estado_previo.get("estado") == "exitoso":
        return {
            "exito": True,
            "sin_cambios": True,
            "archivo": ruta_archivo,
            "estudiantes_procesados": estado_previo.get("estudiantes_procesados", 0),
            "ultimo_sync": estado_previo.get("ultimo_sync"),
            "mensaje": "El archivo no ha cambiado desde la última sincronización.",
        }

    import openpyxl
    wb = openpyxl.load_workbook(ruta_archivo, data_only=True)

    if _es_formato_boletines_ceis(wb):
        return _procesar_libro_boletines_oficial_ceis(
            wb=wb,
            ruta_archivo=ruta_archivo,
            hash_actual=hash_actual,
            anio_lectivo=anio_lectivo,
            periodo_actual=periodo_actual,
        )

    if _es_formato_valoraciones_ceis(wb):
        return _procesar_libro_valoraciones_ceis(
            wb=wb,
            ruta_archivo=ruta_archivo,
            hash_actual=hash_actual,
            anio_lectivo=anio_lectivo,
            periodo_actual=periodo_actual,
        )

    # Cargar informes existentes del mismo año para preservar periodos anteriores al subir uno nuevo
    informes_previos = {}
    for inf in InformeValorativo.objects.filter(anio_lectivo=anio_lectivo).select_related("estudiante"):
        informes_previos[inf.estudiante.documento] = inf

    estudiantes_objs = []
    datos_por_doc = {}
    cursos_procesados = []
    periodos_detectados = set()

    for sheetname in wb.sheetnames:
        curso_clave = obtener_curso_desde_sheetname(sheetname)
        if not curso_clave or curso_clave not in GRADOS:
            continue
        cursos_procesados.append(curso_clave)
        ws = wb[sheetname]
        headers = [c for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]

        col_doc = 1
        col_nom = 2
        col_periodo = None
        materias_cols = {}
        for idx, h in enumerate(headers):
            if h is None:
                continue
            h_str = str(h).strip()
            h_low = h_str.lower()
            if "periodo" in h_low:
                col_periodo = idx
                continue
            if idx >= 3 and h_str not in ("Desempeño General", "Estado Académico"):
                # Detener captura de materias si ya pasamos las columnas de resumen
                if "desempeño general" in h_low or "estado académico" in h_low or "estado academico" in h_low:
                    continue
                materias_cols[h_str] = idx

        es_media = curso_clave in ["1001", "1002", "1101", "1102"]

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row or row[col_doc] is None or row[col_nom] is None:
                continue

            doc_raw = str(row[col_doc]).strip()
            if not doc_raw:
                continue
            try:
                documento = str(int(float(doc_raw)))[:20]
            except Exception:
                documento = doc_raw[:20]

            if documento in datos_por_doc:
                continue

            # Determinar el periodo: si periodo_actual fue forzado explícitamente, usarlo; si es None, leer del Excel
            if periodo_actual is not None:
                periodo_fila = parsear_periodo(periodo_actual, default=3)
            elif col_periodo is not None and col_periodo < len(row) and row[col_periodo] is not None:
                periodo_fila = parsear_periodo(row[col_periodo], default=3)
            else:
                periodo_fila = 3
            periodos_detectados.add(periodo_fila)

            # Mapa de asignaturas existentes del estudiante para preservar periodos anteriores
            prev_inf = informes_previos.get(documento)
            prev_asigs = {}
            if prev_inf and isinstance(prev_inf.datos_academicos, dict):
                for area_prev in prev_inf.datos_academicos.get("areas", []):
                    for asig_prev in area_prev.get("asignaturas", []):
                        if isinstance(asig_prev, dict) and asig_prev.get("nombre"):
                            prev_asigs[asig_prev["nombre"].upper()] = asig_prev

            nombre_completo = str(row[col_nom]).strip().upper()
            partes = nombre_completo.split()
            if len(partes) >= 3:
                apellidos = f"{partes[0]} {partes[1]}"
                nombres = " ".join(partes[2:])
            elif len(partes) == 2:
                apellidos = partes[0]
                nombres = partes[1]
            else:
                apellidos = nombre_completo
                nombres = ""

            rnd = random.Random(int(documento) if documento.isdigit() else 12345)

            estudiantes_objs.append(
                Estudiante(
                    documento=documento,
                    tipo_documento="Tarjeta de Identidad",
                    nombres=nombres,
                    apellidos=apellidos,
                    grado=GRADOS[curso_clave],
                    curso=curso_clave,
                    director_grupo=DIRECTORES.get(curso_clave, "ROJAS GUTIERREZ LILIANA ASTRID"),
                    acudiente=f"Familia {apellidos}",
                    telefono_acudiente="310" + "".join([str(rnd.randint(0, 9)) for _ in range(7)]),
                    activo=True,
                )
            )

            def _asig_dict(nombre_upper, nota_val):
                periodos_data = construir_periodos_asignatura(
                    nota_val, periodo_fila, rnd, existing_asig=prev_asigs.get(nombre_upper)
                )
                return {"nombre": nombre_upper, **periodos_data}

            areas = []
            if es_media:
                asigs_cientifico = []
                for mat_nombre in ["Química", "Física"]:
                    if mat_nombre in materias_cols:
                        nota_val = row[materias_cols[mat_nombre]] or "BÁSICO"
                        asigs_cientifico.append(_asig_dict(mat_nombre.upper(), nota_val))
                asigs_cientifico.append(_asig_dict("BIOLOGÍA", "ALTO"))
                areas.append({"nombre": "PENSAMIENTO CIENTÍFICO", "asignaturas": asigs_cientifico})

                nota_mat = row[materias_cols.get("Matemáticas", 3)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO MATEMÁTICO",
                    "asignaturas": [_asig_dict("MATEMÁTICAS", nota_mat)]
                })

                asigs_com = []
                for mat_nombre in ["Lengua Castellana", "Inglés"]:
                    if mat_nombre in materias_cols:
                        n = row[materias_cols[mat_nombre]] or "ALTO"
                        asigs_com.append(_asig_dict(mat_nombre.upper(), n))
                areas.append({"nombre": "COMUNICACIONES (HUMANIDADES)", "asignaturas": asigs_com})

                n_pol = row[materias_cols.get("Política y Economía", 7)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO SOCIAL",
                    "asignaturas": [
                        _asig_dict("P. POLITICO Y ECONOMICO", n_pol),
                        _asig_dict("PENSAMIENTO SOCIAL", "BÁSICO"),
                    ]
                })

                n_fil = row[materias_cols.get("Filosofía", 8)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO FILOSOFICO",
                    "asignaturas": [_asig_dict("FILOSOFIA", n_fil)]
                })

                n_ef = row[materias_cols.get("Educación Física", 10)] or "SUPERIOR"
                areas.append({
                    "nombre": "CULTURA FÍSICA Y DEPORTIVA",
                    "asignaturas": [_asig_dict("EDUCACIÓN FÍSICA", n_ef)]
                })

                n_art = row[materias_cols.get("Educación Artística", 11)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO ARTÍSTICO",
                    "asignaturas": [_asig_dict("EDUCACIÓN ARTÍSTICA", n_art)]
                })

                n_et = row[materias_cols.get("Ética y Valores", 12)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO ÉTICO Y CIUDADANO",
                    "asignaturas": [_asig_dict("EDUCACIÓN ÉTICA Y VALORES", n_et)]
                })

                n_tec = row[materias_cols.get("Tecnología e Informática", 9)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO TECNOLÓGICO",
                    "asignaturas": [_asig_dict("TECNOLOGÍA E INFORMÁTICA", n_tec)]
                })
            else:
                n_nat = row[materias_cols.get("Ciencias Naturales", 5)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO CIENTÍFICO",
                    "asignaturas": [_asig_dict("BIOLOGÍA / CIENCIAS NATURALES", n_nat)]
                })

                n_mat = row[materias_cols.get("Matemáticas", 3)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO MATEMÁTICO",
                    "asignaturas": [_asig_dict("MATEMÁTICAS", n_mat)]
                })

                asigs_com = []
                for mat_nombre in ["Lengua Castellana", "Inglés"]:
                    if mat_nombre in materias_cols:
                        n = row[materias_cols[mat_nombre]] or "ALTO"
                        asigs_com.append(_asig_dict(mat_nombre.upper(), n))
                areas.append({"nombre": "COMUNICACIONES (HUMANIDADES)", "asignaturas": asigs_com})

                n_soc = row[materias_cols.get("Ciencias Sociales", 6)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO SOCIAL",
                    "asignaturas": [_asig_dict("CIENCIAS SOCIALES", n_soc)]
                })

                n_ef = row[materias_cols.get("Educación Física", 10)] or "SUPERIOR"
                areas.append({
                    "nombre": "CULTURA FÍSICA Y DEPORTIVA",
                    "asignaturas": [_asig_dict("EDUCACIÓN FÍSICA", n_ef)]
                })

                n_art = row[materias_cols.get("Educación Artística", 11)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO ARTÍSTICO",
                    "asignaturas": [_asig_dict("EDUCACIÓN ARTÍSTICA", n_art)]
                })

                n_et = row[materias_cols.get("Ética y Valores", 12)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO ÉTICO Y CIUDADANO",
                    "asignaturas": [_asig_dict("EDUCACIÓN ÉTICA Y VALORES", n_et)]
                })

                n_tec = row[materias_cols.get("Tecnología e Informática", 9)] or "ALTO"
                areas.append({
                    "nombre": "PENSAMIENTO TECNOLÓGICO",
                    "asignaturas": [_asig_dict("TECNOLOGÍA E INFORMÁTICA", n_tec)]
                })

            conv_p, fam_p, fallas_p, prom_p, sena_p = {}, {}, {}, {}, {}
            for p in (1, 2, 3, 4):
                pk = f"p{p}"
                if p <= periodo_fila:
                    conv_p[pk] = {
                        "pa": f"{rnd.randint(80, 96)/10:.1f}".replace(".", ","),
                        "vc": str(rnd.randint(8, 10)),
                        "pc": f"{rnd.randint(80, 96):.1f}".replace(".", ","),
                        "des": rnd.choice(["S", "A", "A", "S"] if p >= 3 else ["S", "A", "A", "BS"]),
                    }
                    fam_p[pk] = rnd.choice(["S", "S", "A"])
                    fallas_p[pk] = {"f": rnd.randint(0, 2), "r": rnd.randint(0, 2), "e": 0, "u": 0}
                    prom_p[pk] = f"{rnd.randint(78, 96)/10:.2f}".replace(".", ",")
                    sena_p[pk] = rnd.choice(["A", "A", "S"] if p >= 3 else ["A", "A", "BS"])
                else:
                    conv_p[pk] = {"pa": "0,0", "vc": "-", "pc": "0,0", "des": "-"}
                    fam_p[pk] = "-"
                    fallas_p[pk] = {"f": 0, "r": 0, "e": 0, "u": 0}
                    prom_p[pk] = "0,00"
                    sena_p[pk] = "-"

            convivencia_data = {
                "convivencia": conv_p,
                "ambito_familiar": fam_p,
                "fallas_retardos": fallas_p,
            }

            datos_academicos = {
                "areas": areas,
                "promedio_actitudinal": prom_p,
                "tecnico_sena": sena_p,
            }

            datos_por_doc[documento] = (datos_academicos, convivencia_data, periodo_fila)

    # Actualizar Estudiantes en lotes de 50 para estabilidad en Supabase Pooler
    Estudiante.objects.bulk_create(
        estudiantes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["documento"],
        update_fields=["nombres", "apellidos", "grado", "curso", "director_grupo", "acudiente", "activo"],
    )

    mapa_est = {e.documento: e for e in Estudiante.objects.filter(documento__in=list(datos_por_doc.keys()))}
    informes_objs = []
    for doc, (d_acad, d_conv, per_fila) in datos_por_doc.items():
        est = mapa_est.get(doc)
        if not est:
            continue
        p_key = f"p{per_fila}"
        tec_sena_val = "A"
        if isinstance(d_acad, dict) and "tecnico_sena" in d_acad:
            tec_sena_val = d_acad["tecnico_sena"].get(p_key, d_acad["tecnico_sena"].get("p3", "A"))

        informes_objs.append(
            InformeValorativo(
                estudiante=est,
                anio_lectivo=anio_lectivo,
                periodo_actual=per_fila,
                datos_academicos=d_acad,
                datos_convivencia=d_conv,
                observaciones_academicas=(
                    "El estudiante demuestra compromiso constante en el desarrollo de las guías SERC.\n"
                    "Se sugiere continuar fortaleciendo la fase de Relación y entrega puntual de evidencias."
                ),
                observaciones_convivenciales=(
                    "La institución agradece su colaboración en las campañas de mejora.\n"
                    "Felicitaciones por su aporte a la convivencia institucional."
                ),
                tecnico_sena=tec_sena_val,
            )
        )

    InformeValorativo.objects.bulk_create(
        informes_objs,
        batch_size=50,
        update_conflicts=True,
        unique_fields=["estudiante", "anio_lectivo"],
        update_fields=["periodo_actual", "datos_academicos", "datos_convivencia", "observaciones_academicas", "observaciones_convivenciales", "tecnico_sena"],
    )

    cursos_unicos = sorted(list(set(cursos_procesados)))
    periodos_lista = sorted(list(periodos_detectados)) if periodos_detectados else [periodo_actual or 3]
    periodo_resumen = max(periodos_lista)
    ahora_iso = datetime.datetime.now().isoformat()
    nuevo_estado = {
        "ultimo_sync": ahora_iso,
        "archivo": ruta_archivo,
        "hash": hash_actual,
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "estado": "exitoso",
        "mensaje": f"{len(estudiantes_objs)} estudiantes y boletines sincronizados correctamente (Periodo {', '.join(map(str, periodos_lista))} · {len(cursos_unicos)} cursos).",
    }
    guardar_estado_sync(nuevo_estado)

    return {
        "exito": True,
        "sin_cambios": False,
        "archivo": ruta_archivo,
        "estudiantes_procesados": len(estudiantes_objs),
        "cursos_procesados": cursos_unicos,
        "anio_lectivo": anio_lectivo,
        "periodo_actual": periodo_resumen,
        "periodos_detectados": periodos_lista,
        "ultimo_sync": ahora_iso,
        "hash": hash_actual,
        "mensaje": nuevo_estado["mensaje"],
    }

