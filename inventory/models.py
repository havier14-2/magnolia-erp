from django.db import models
from django.contrib.auth.models import User

# ==========================================
# 1. CATÁLOGO E INSUMOS
# ==========================================
class Insumo(models.Model):
    UNIDADES = [
        ('gr', 'Gramos'),
        ('ml', 'Mililitros'),
        ('un', 'Unidades'),
    ]

    nombre = models.CharField(max_length=100, unique=True)
    unidad_medida = models.CharField(max_length=2, choices=UNIDADES)
    costo_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    stock_actual = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    alerta_minimo = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.nombre} ({self.get_unidad_medida_display()})"

# ==========================================
# 2. RECETAS (ESCANDALLOS)
# ==========================================
class Receta(models.Model):
    nombre_producto = models.CharField(max_length=100, unique=True, help_text="Nombre exacto que viene en el Excel de Fudo")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ingredientes = models.ManyToManyField(Insumo, through='IngredienteReceta')

    def __str__(self):
        return self.nombre_producto

    @property
    def costo_total_produccion(self):
        """Calcula el costo total sumando (cantidad * costo_unitario) de cada ingrediente."""
        total = 0
        ingredientes = IngredienteReceta.objects.filter(receta=self)
        for item in ingredientes:
            total += (item.cantidad_necesaria * item.insumo.costo_unitario)
        return total

    @property
    def margen_ganancia(self):
        """Diferencia entre precio de venta y costo de producción."""
        return self.precio_venta - self.costo_total_produccion

class IngredienteReceta(models.Model):
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.CASCADE)
    cantidad_necesaria = models.DecimalField(max_digits=10, decimal_places=3, help_text="Cantidad en la unidad de medida del insumo (ej: gramos o ml)")

    class Meta:
        unique_together = ['insumo', 'receta'] # Evita agregar dos veces el mismo ingrediente a una receta

    def __str__(self):
        return f"{self.cantidad_necesaria} {self.insumo.unidad_medida} de {self.insumo.nombre} en {self.receta.nombre_producto}"
    # NUEVO: Calculadora de subtotal
    @property
    def costo_total_produccion(self):
        """Calcula el costo total usando la relación en memoria para evitar N+1 queries."""
        total = 0
        # Cambiamos IngredienteReceta.objects.filter(...) por .all() sobre el set relacional
        for item in self.ingredientereceta_set.all():
            total += (item.cantidad_necesaria * item.insumo.costo_unitario)
        return total
# ==========================================
# 3. VENTAS (INGESTA CSV)
# ==========================================
class Venta(models.Model):
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    archivo_origen = models.CharField(max_length=255, blank=True, null=True, help_text="Nombre del archivo CSV de Fudo")

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name='detalles', on_delete=models.CASCADE)
    receta = models.ForeignKey(Receta, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()
    precio_unitario_historico = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.cantidad}x {self.receta.nombre_producto} (Venta #{self.venta.id})"

# ==========================================
# 4. KARDEX Y AUDITORÍA INMUTABLE
# ==========================================
class MovimientoStock(models.Model):
    TIPOS = [
        ('entrada', 'Entrada (Compra/Ajuste)'),
        ('salida', 'Salida (Venta/Merma)'),
    ]
    
    insumo = models.ForeignKey(Insumo, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.DecimalField(max_digits=10, decimal_places=3)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    observacion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Movimiento de Stock"
        verbose_name_plural = "Movimientos (Kardex)"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.insumo.nombre}: {self.cantidad} {self.insumo.unidad_medida}"