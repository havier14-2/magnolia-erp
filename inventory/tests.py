from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from unittest.mock import patch

from django.test import TestCase
from decimal import Decimal
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch
from .models import Insumo, Receta, IngredienteReceta

class RecetaModelTest(TestCase):
    def setUp(self):
        """
        El equivalente a @BeforeEach en JUnit. 
        Preparamos los datos en la base de datos temporal antes de cada prueba.
        """
        self.insumo_cafe = Insumo.objects.create(
            nombre="Café de Especialidad", 
            unidad_medida="gr", 
            costo_unitario=Decimal('20.0'), # $20 por gramo
            stock_actual=Decimal('1000')
        )
        self.receta_espresso = Receta.objects.create(
            nombre_producto="Espresso Doble", 
            precio_venta=Decimal('2000.0') # Se vende a $2000
        )
        # Asignamos 18 gramos de café al Espresso
        IngredienteReceta.objects.create(
            receta=self.receta_espresso, 
            insumo=self.insumo_cafe, 
            cantidad_necesaria=Decimal('18.0')
        )

    def test_calculo_costo_y_margen_exacto(self):
        """Prueba que la lógica financiera del modelo funcione impecable."""
        # 1. Validar Food Cost: 18 gramos * $20 = $360
        self.assertEqual(self.receta_espresso.costo_total_produccion, Decimal('360.0'))
        
        # 2. Validar Margen Neto: $2000 (Venta) - $360 (Costo) = $1640
        self.assertEqual(self.receta_espresso.margen_ganancia, Decimal('1640.0'))




class DashboardYSeguridadTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(username='admin_test', password='password123')
        self.url_dashboard = reverse('dashboard') # Asegúrate de que este 'name' exista en urls.py

    def test_dashboard_protegido_sin_login(self):
        """Si un intruso intenta entrar al dashboard, debe ser redirigido al login."""
        response = self.client.get(self.url_dashboard)
        self.assertRedirects(response, f'/accounts/login/?next={self.url_dashboard}')

    def test_dashboard_acceso_con_login(self):
        """Un usuario autenticado debe ver la pantalla y los KPIs correctos."""
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(self.url_dashboard)
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'inventory/dashboard.html')
        # Verificamos que el contexto (las variables que van al HTML) existan
        self.assertIn('kpi_valor_total', response.context)

    # ==========================================
    # EJEMPLO MOCKITO EN PYTHON (@patch)
    # ==========================================
    @patch('inventory.views.DashboardView.get_context_data')
    def test_dashboard_con_kpis_simulados(self, mock_get_context):
        """
        Interceptamos el método real y le inyectamos datos falsos (Mock).
        Útil cuando quieres probar la vista sin tocar la base de datos pesada.
        """
        # Configuramos el Mock para que devuelva un valor estático
        mock_get_context.return_value = {
            'kpi_valor_total': Decimal('99999.0'),
            'kpi_alertas': 0,
            'kpi_recetas': 10
        }
        
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(self.url_dashboard)
        
        # Validamos que el Mock haya inyectado nuestra data falsa con éxito
        self.assertEqual(response.context['kpi_valor_total'], Decimal('99999.0'))





# El decorador 'override_settings' activa el "Modo Impaciente".
# Hace que Celery ejecute la tarea de inmediato para poder testearla.
@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class FudoSyncYCeleryTest(TestCase):
    def setUp(self):
        # 1. Creamos un usuario con permisos
        self.user = User.objects.create_superuser(username='admin_fudo', password='password123')
        self.client.login(username='admin_fudo', password='password123')
        
        # 2. Conectamos con el nombre exacto de tu urls.py
        self.url_sincronizacion = reverse('sincronizar_ventas') 

    def test_subida_archivo_y_ejecucion_asincrona(self):
        """Simula la subida de un CSV y verifica la respuesta de la vista."""
        
        # 1. Fabricamos un archivo CSV falso directamente en la memoria RAM
        contenido_csv = b"fecha,producto,cantidad,total\n2026-06-17,Espresso,2,4000\n"
        archivo_simulado = SimpleUploadedFile(
            name="ventas_prueba.csv", 
            content=contenido_csv, 
            content_type="text/csv"
        )
        
        # 2. Hacemos el POST usando el 'name' exacto de tu HTML (archivo_ventas)
        response = self.client.post(self.url_sincronizacion, {'archivo_ventas': archivo_simulado})
        
        # 3. Validamos que la respuesta del servidor sea exitosa o una redirección
        self.assertIn(response.status_code, [200, 302]) 

    # Conectamos el Mock con el nombre exacto de tu función en tasks.py
    @patch('inventory.tasks.procesar_archivo_ventas_rabbitmq.delay') 
    def test_vista_dispara_rabbitmq_correctamente(self, mock_celery_delay):
        """
        Prueba con Mockito puro: Verificamos que la vista intentó contactar 
        a Celery/RabbitMQ al aislar la tarea pesada.
        """
        archivo_simulado = SimpleUploadedFile(
            name="ventas.csv", content=b"dummy data", content_type="text/csv"
        )
        
        # Simulamos el POST a tu vista
        self.client.post(self.url_sincronizacion, {'archivo_ventas': archivo_simulado})
        
        # ¡La aserción maestra! Verificamos que tu vista llamó a .delay()
        mock_celery_delay.assert_called_once()