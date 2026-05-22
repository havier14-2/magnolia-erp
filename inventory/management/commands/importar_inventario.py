import pandas as pd
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.db import transaction
from inventory.models import Insumo

class Command(BaseCommand):
    help = 'Importa el inventario desde un Excel con formato de bloques/categorías'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta al archivo Excel (.xlsx)')

    def handle(self, *args, **kwargs):
        excel_path = kwargs['excel_file']

        try:
            self.stdout.write(self.style.WARNING(f'⏳ Leyendo archivo Excel en modo "Bloques": {excel_path}...'))
            
            # 1. Leer el Excel SIN cabeceras (header=None) para procesar todo crudo
            df = pd.read_excel(excel_path, header=None)
            df = df.fillna('')

            with transaction.atomic():
                filas_procesadas = 0
                
                # 2. Iterar sobre las filas
                for index, row in df.iterrows():
                    # En tu Excel: Columna 0 está vacía, Columna 1 es Nombre, Col 2 es Unidad, Col 3 es Cantidad
                    try:
                        nombre_raw = str(row[1]).strip()
                        unidad_raw = str(row[2]).strip().lower()
                        stock_raw = str(row[3]).strip().replace(',', '.')
                    except KeyError:
                        # Si la fila no tiene suficientes columnas, la ignoramos
                        continue

                    # 3. Filtros de exclusión (Saltar basura y cabeceras)
                    if not nombre_raw or nombre_raw.lower() == 'nan':
                        continue 
                    
                    # Si la columna de unidad dice "unidad" literalmente, es una fila de título (ej: Abarrotes | Unidad | Cantidad)
                    if unidad_raw == 'unidad' or unidad_raw == 'medida':
                        continue

                    # 4. Mapeo de unidades al estándar de la BD
                    unidad_final = 'un' 
                    if unidad_raw in ['gr', 'g', 'gramos', 'gramo', 'kg', 'kilo', 'kilogramos']:
                        unidad_final = 'gr'
                    elif unidad_raw in ['ml', 'lt', 'litro', 'litros', 'cc']:
                        unidad_final = 'ml'

                    # 5. Conversión de Stock (Si está vacía en el Excel, queda en 0)
                    try:
                        stock_limpio = Decimal(float(stock_raw)) if stock_raw else Decimal('0.00')
                    except (InvalidOperation, ValueError):
                        stock_limpio = Decimal('0.00')

                    # Como este Excel no tiene costo, lo inicializamos en 0
                    costo_limpio = Decimal('0.00')

                    # 6. Guardar en la Base de Datos
                    Insumo.objects.update_or_create(
                        nombre=nombre_raw,
                        defaults={
                            'unidad_medida': unidad_final,
                            'costo_unitario': costo_limpio, # Se actualizará después desde la app
                            'stock_actual': stock_limpio,
                            'alerta_minimo': Decimal('0.00')
                        }
                    )
                    
                    filas_procesadas += 1

                self.stdout.write(self.style.SUCCESS(f'✅ ¡Éxito! Se procesaron {filas_procesadas} insumos saltando las cabeceras.'))

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ Error: No se encontró el archivo {excel_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ocurrió un error inesperado: {str(e)}'))