from celery import shared_task
import time

@shared_task
def procesar_archivo_ventas(archivo_id):
    """
    Simulación del procesamiento de un CSV pesado.
    Aquí irá la lógica de leer el CSV, buscar recetas, descontar Kardex, etc.
    """
    print(f"=== INICIANDO === Procesando el archivo CSV de ventas ID: {archivo_id}")
    
    # Simulamos un proceso pesado que toma 10 segundos
    time.sleep(10)
    
    print(f"=== FINALIZADO === Archivo {archivo_id} procesado y Kardex actualizado.")
    return True