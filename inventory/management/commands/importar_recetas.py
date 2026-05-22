import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Receta

class Command(BaseCommand):
    help = 'Importa los productos de la carta leyendo el Excel sin cabeceras'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta al archivo Excel (.xlsx)')

    def handle(self, *args, **kwargs):
        excel_path = kwargs['excel_file']

        try:
            self.stdout.write(self.style.WARNING(f'⏳ Leyendo carta en modo crudo: {excel_path}...'))
            
            # 1. Leer el Excel SIN cabeceras (header=None) para procesar todo crudo
            df = pd.read_excel(excel_path, header=None)
            df = df.fillna('')

            with transaction.atomic():
                filas_procesadas = 0
                
                # 2. Iterar sobre las filas
                for index, row in df.iterrows():
                    try:
                        # En tu Excel de Productos: Columna 0 está vacía, Columna 1 es el Nombre, Col 2 es Categoría
                        nombre_raw = str(row[1]).strip()
                    except KeyError:
                        continue

                    # 3. Filtros de exclusión (Saltar basura y la palabra literal "Nombre")
                    if not nombre_raw or nombre_raw.lower() == 'nan':
                        continue 
                    
                    if nombre_raw.lower() == 'nombre':
                        continue

                    # 4. Como este archivo no trae precio de venta, lo iniciamos en 0
                    precio_limpio = Decimal('0.00')

                    # 5. Guardar en la Base de Datos
                    Receta.objects.update_or_create(
                        nombre_producto=nombre_raw,
                        defaults={
                            'precio_venta': precio_limpio
                        }
                    )
                    
                    filas_procesadas += 1

                self.stdout.write(self.style.SUCCESS(f'✅ ¡Éxito! Se cargaron {filas_procesadas} productos a la carta.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ Error: No se encontró el archivo {excel_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ocurrió un error inesperado: {str(e)}'))