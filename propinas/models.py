from django.db import models
from django.contrib.auth.models import User

# 1. EL CEREBRO: Las Reglas configurables
class ReglaDistribucion(models.Model):
    nombre_rol = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Rol")
    porcentaje_am = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Porcentaje Turno AM (%)"
    )
    porcentaje_pm = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0,
        verbose_name="Porcentaje Turno PM (%)"
    )
    activo = models.BooleanField(default=True, help_text="Desmarcar para ocultar este rol sin borrarlo")

    class Meta:
        verbose_name = "Regla de Distribución"
        verbose_name_plural = "Reglas de Distribución"
        ordering = ['-porcentaje_am']

    def __str__(self):
        return f"{self.nombre_rol} (AM: {self.porcentaje_am}% | PM: {self.porcentaje_pm}%)"


# 2. EL EVENTO: El Turno del día
class Turno(models.Model):
    TIPO_TURNO = [
        ('AM', 'Mañana'),
        ('PM', 'Tarde'),
    ]
    
    fecha = models.DateField()
    tipo = models.CharField(max_length=2, choices=TIPO_TURNO)
    
    # El pozo a repartir
    propinas_sistema = models.IntegerField(default=0, help_text="Propinas registradas en FUDO")
    efectivo = models.IntegerField(default=0, help_text="Propinas en efectivo")
    
    # Control de estado
    cerrado = models.BooleanField(default=False, help_text="Si está cerrado, no se puede modificar")
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['fecha', 'tipo'] # Solo puede haber un turno AM por día
        ordering = ['-fecha', 'tipo']

    @property
    def total_pozo(self):
        return self.propinas_sistema + self.efectivo

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.fecha} (${self.total_pozo})"


# 3. EL MÚSCULO: Quién trabajó y cuánto ganó
class ParticipanteTurno(models.Model):
    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name='participantes')
    empleado = models.ForeignKey(User, on_delete=models.PROTECT)
    rol = models.ForeignKey(ReglaDistribucion, on_delete=models.PROTECT)
    
    # El resultado final que calculará nuestro algoritmo
    monto_asignado = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        unique_together = ['turno', 'empleado'] # Un empleado no puede estar 2 veces en el mismo turno

    def __str__(self):
        return f"{self.empleado.username} - {self.rol.nombre_rol} (${self.monto_asignado})"