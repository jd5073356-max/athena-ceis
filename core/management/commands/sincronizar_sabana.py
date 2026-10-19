"""Comando de gestión Django para sincronizar la sábana Excel con la base de datos."""
from django.core.management.base import BaseCommand
from core.sync_service import ejecutar_sincronizacion_excel, leer_estado_sync


class Command(BaseCommand):
    help = "Sincroniza la sábana de notas Excel con la base de datos PostgreSQL/Supabase."

    def add_arguments(self, parser):
        parser.add_argument(
            "--archivo",
            type=str,
            default=None,
            help="Ruta alternativa del archivo Excel de la sábana de notas.",
        )
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Fuerza la importación incluso si el archivo no ha cambiado.",
        )

    def handle(self, *args, **options):
        archivo = options.get("archivo")
        forzar = options.get("forzar", False)

        self.stdout.write("Iniciando sincronización de sábana de notas...")
        resultado = ejecutar_sincronizacion_excel(ruta_archivo=archivo, forzar=forzar)

        if resultado.get("exito"):
            if resultado.get("sin_cambios"):
                self.stdout.write(self.style.WARNING(resultado.get("mensaje", "Sin cambios detectados.")))
            else:
                self.stdout.write(self.style.SUCCESS(resultado.get("mensaje", "Sincronización completada con éxito.")))
        else:
            self.stdout.write(self.style.ERROR(f"Error en sincronización: {resultado.get('error')}"))
