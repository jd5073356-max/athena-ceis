#!/usr/bin/env python3
"""
Athena — Script de Keep-Alive para Supabase PostgreSQL

Ejecuta una consulta liviana contra Supabase PostgreSQL para mantener la base de datos
activa 24/7 y prevenir la pausa automática del plan gratuito por 7 días de inactividad.
"""
import os
import sys
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
os.environ.setdefault("DB_ENGINE", "postgres")

import django
django.setup()

from django.db import connection

def run_keep_alive():
    now = datetime.datetime.now().isoformat()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            result = cursor.fetchone()
            if result and result[0] == 1:
                print(f"[{now}] ✅ Keep-Alive Supabase PostgreSQL: OK (SELECT 1 respondido)")
                return True
            else:
                print(f"[{now}] ⚠️ Keep-Alive Supabase PostgreSQL: Respuesta inesperada {result}")
                return False
    except Exception as e:
        print(f"[{now}] ❌ Error en Keep-Alive Supabase PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    success = run_keep_alive()
    sys.exit(0 if success else 1)
