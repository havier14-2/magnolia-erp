import logging
from celery import shared_task
from django.db import transaction, DatabaseError
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth.models import User
from .models import Receta, MovimientoStock

# Usamos el logger profesional en lugar de "print"
logger = logging.getLogger(__name__)

# bind=True permite acceder a 'self' para reintentar. max_retries evita bucles infinitos.
@shared_task(bind=True, max_retries=3, default_retry_delay=5)
def procesar_archivo_ventas_rabbitmq(self, ventas_validas, usuario_id):
    """
    Worker de Celery: Consume los mensajes de RabbitMQ y actualiza la BD de forma segura.
    """
    logger.info(f"[RabbitMQ] Tarea iniciada. Procesando {len(ventas_validas)} registros de Fudo.")
    
    try:
        usuario = User.objects.get(id=usuario_id)
    except User.DoesNotExist:
        usuario = None
        logger.warning("[RabbitMQ] Usuario no encontrado. El Kardex quedará sin autor.")

    try:
        # Escudo atómico: O se procesan todos los insumos, o no se procesa ninguno.
        with transaction.atomic():
            descuentos_totales = {}
            
            # 1. Agrupar la matemática en memoria RAM
            for item in ventas_validas:
                receta = Receta.objects.get(id=item['receta_id'])
                cantidad_vendida = Decimal(str(item['cantidad'])).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                
                for ing in receta.ingredientereceta_set.select_related('insumo').all():
                    gasto = (Decimal(str(ing.cantidad_necesaria)) * cantidad_vendida).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    
                    if ing.insumo in descuentos_totales:
                        descuentos_totales[ing.insumo] += gasto
                    else:
                        descuentos_totales[ing.insumo] = gasto

            # 2. Impactar la base de datos de una sola vez
            for insumo, total_descuento in descuentos_totales.items():
                insumo.stock_actual -= total_descuento
                insumo.save()

                MovimientoStock.objects.create(
                    insumo=insumo,
                    tipo='salida',
                    cantidad=total_descuento,
                    usuario=usuario,
                    observacion="Descuento automático (Sincronización Fudo vía RabbitMQ)"
                )

        logger.info("[RabbitMQ] Tarea finalizada con éxito. Kardex actualizado.")
        return "Sincronización Completada"

    except DatabaseError as e:
        # Si Neon (PostgreSQL) está bloqueado, reintentamos en 5 segundos
        logger.error(f"[RabbitMQ] Bloqueo de base de datos. Reintentando... Detalle: {str(e)}")
        raise self.retry(exc=e)
        
    except Exception as e:
        logger.critical(f"[RabbitMQ] Error fatal en la tarea. Rollback ejecutado. Detalle: {str(e)}")
        # No reintentamos errores de código, solo los registramos
        return False