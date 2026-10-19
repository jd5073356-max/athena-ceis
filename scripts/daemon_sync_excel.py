#!/usr/bin/env python3
"""Daemon de sincronización continua de sábana Excel a base de datos PostgreSQL cada 5 minutos."""
import os
import sys
import time
import signal
import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
django.setup()

from core.sync_service import ejecutar_sincronizacion_excel, obtener_ruta_excel_activa

INTERVALO_SEGUNDOS = 300  # 5 minutos
EJECUTANDO = True


def manejar_parada(signum, frame):
    global EJECUTANDO
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Deteniendo daemon de sincronización Excel...")
    EJECUTANDO = False


signal.signal(signal.SIGINT, manejar_parada)
signal.signal(signal.SIGTERM, manejar_parada)


def iniciar_daemon():
    print("=" * 70)
    print("DAEMON DE SINCRONIZACIÓN CONTINUA - EXCEL A POSTGRESQL (SERC / ATHENA)")
    print(f"Intervalo: cada {INTERVALO_SEGUNDOS // 60} minutos ({INTERVALO_SEGUNDOS} segundos)")
    print(f"Directorio base: {BASE_DIR}")
    print("=" * 70)

    while EJECUTANDO:
        marca_tiempo = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ruta_archivo = obtener_ruta_excel_activa()

        if not ruta_archivo:
            print(f"[{marca_tiempo}] ALERTA: No se encontró ningún archivo de sábana Excel activo.")
        else:
            print(f"[{marca_tiempo}] Verificando sincronización: {ruta_archivo}")
            try:
                # Comprobar si hubo cambios o ejecutar sync
                resultado = ejecutar_sincronizacion_excel(ruta_archivo=ruta_archivo, forzar=False)
                if resultado.get("exito"):
                    if resultado.get("sin_cambios"):
                        print(f"[{marca_tiempo}] Estado: Sin cambios en el archivo. Base de datos al día ({resultado.get('estudiantes_procesados')} registros).")
                    else:
                        print(f"[{marca_tiempo}] ÉXITO: {resultado.get('mensaje')}")
                else:
                    print(f"[{marca_tiempo}] ERROR: {resultado.get('error')}")
            except Exception as e:
                print(f"[{marca_tiempo}] EXCEPCIÓN durante sincronización: {e}")

        # Esperar 5 minutos verificando señal de parada
        segundos_esperados = 0
        while EJECUTANDO and segundos_esperados < INTERVALO_SEGUNDOS:
            time.sleep(1)
            segundos_esperados += 1

    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Daemon finalizado de forma controlada.")


if __name__ == "__main__":
    iniciar_daemon()
