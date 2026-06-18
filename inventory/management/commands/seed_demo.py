from django.core.management.base import BaseCommand
from inventory.models import Insumo, Receta, IngredienteReceta
from decimal import Decimal

class Command(BaseCommand):
    help = 'Inyecta datos realistas de cafetería de especialidad adaptados al modelo Magnolia'

    def handle(self, *args, **kwargs):
        self.stdout.write("1. Limpiando datos de prueba antiguos...")
        # Eliminamos registros anteriores que ensucian los gráficos
        Insumo.objects.filter(nombre__icontains='javier').delete()
        Insumo.objects.filter(nombre__icontains='Agua sabor').delete()
        
        self.stdout.write("2. Abasteciendo la bodega con Insumos Reales...")
        # Mapeo exacto: nombre, unidad_medida (max 2 chars), costo_unitario, stock_actual, alerta_minimo
        insumos_data = [
            {'nombre': 'Café Etiopía Lavado (Grano)', 'unidad': 'gr', 'costo': '35.0', 'stock': '5000', 'alerta': '1000'},
            {'nombre': 'Leche Entera Colun', 'unidad': 'ml', 'costo': '1.2', 'stock': '15000', 'alerta': '5000'},
            {'nombre': 'Leche NotMilk Barista', 'unidad': 'ml', 'costo': '2.5', 'stock': '8000', 'alerta': '3000'},
            {'nombre': 'Sirope de Vainilla Monin', 'unidad': 'ml', 'costo': '15.0', 'stock': '2000', 'alerta': '500'},
            {'nombre': 'Vasos Polipapel 8oz', 'unidad': 'un', 'costo': '45.0', 'stock': '40', 'alerta': '200'},  # Alerta activa
            {'nombre': 'Tapas 8oz', 'unidad': 'un', 'costo': '15.0', 'stock': '20', 'alerta': '200'},       # Alerta activa
        ]
        
        insumos_creados = {}
        for item in insumos_data:
            insumo, created = Insumo.objects.update_or_create(
                nombre=item['nombre'],
                defaults={
                    'unidad_medida': item['unidad'],
                    'costo_unitario': Decimal(item['costo']),
                    'stock_actual': Decimal(item['stock']),
                    'alerta_minimo': Decimal(item['alerta'])
                }
            )
            insumos_creados[item['nombre']] = insumo

        self.stdout.write("3. Diseñando la Carta y los Escandallos...")
        # Recetas sincronizadas con los nombres del reporte de Fudo
        recetas_data = [
            {
                'nombre': 'Flat White', 'precio': '3200.00', 
                'ingredientes': [('Café Etiopía Lavado (Grano)', '18'), ('Leche Entera Colun', '150')]
            },
            {
                'nombre': 'Latte Vainilla', 'precio': '3800.00', 
                'ingredientes': [
                    ('Café Etiopía Lavado (Grano)', '18'), 
                    ('Leche Entera Colun', '200'), 
                    ('Sirope de Vainilla Monin', '15'), 
                    ('Vasos Polipapel 8oz', '1'), 
                    ('Tapas 8oz', '1')
                ]
            },
            {
                'nombre': 'Espresso Doble', 'precio': '2200.00', 
                'ingredientes': [('Café Etiopía Lavado (Grano)', '18')]
            },
            {
                'nombre': 'Iced Not Latte', 'precio': '4200.00', 
                'ingredientes': [('Café Etiopía Lavado (Grano)', '18'), ('Leche NotMilk Barista', '200')]
            }
        ]

        for r_data in recetas_data:
            receta, created = Receta.objects.update_or_create(
                nombre_producto=r_data['nombre'],
                defaults={'precio_venta': Decimal(r_data['precio'])}
            )
            
            # Limpiamos relaciones previas para evitar duplicados en la tabla intermedia
            receta.ingredientereceta_set.all().delete()
            
            for ing_nombre, cantidad in r_data['ingredientes']:
                IngredienteReceta.objects.create(
                    receta=receta,
                    insumo=insumos_creados[ing_nombre],
                    cantidad_necesaria=Decimal(cantidad)
                )

        self.stdout.write(self.style.SUCCESS('¡ÉXITO! Base de datos poblada de forma consistente.'))