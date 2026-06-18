from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Insumo
# Modifica tu importación de formularios para incluir el nuevo
from .forms import InsumoForm, IngredienteRecetaForm, RecetaPrecioForm
from django.views import View
from django.db import transaction
from django.urls import reverse_lazy
from .forms import InsumoForm
from .tasks import procesar_archivo_ventas_rabbitmq # Importación de Celery
import io
from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView, DetailView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Insumo, MovimientoStock, Receta, IngredienteReceta
from .forms import InsumoForm, IngredienteRecetaForm
from django.contrib.auth.decorators import login_required
# Create your views here. Inventoryyy
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from decimal import Decimal, ROUND_HALF_UP
from .forms import SincronizacionFudoForm
from django.contrib import messages
from django.views.generic import FormView
import pandas as pd
from thefuzz import process, fuzz
from django.contrib import messages
from django.views.generic import FormView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect

from django.views.generic import TemplateView
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'inventory/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1. Traer todos los datos
        insumos = list(Insumo.objects.all())
        recetas = list(Receta.objects.all())

        # 2. Calcular KPIs Rápidos
        valor_total_bodega = sum(i.stock_actual * i.costo_unitario for i in insumos)
        
        # Alertas de stock (Asumimos alerta si el stock es menor a 10 unidades/gramos)
        alertas_stock = sum(1 for i in insumos if i.stock_actual <= 10)

        # 3. Gráfico 1: Top 5 Insumos con Mayor Capital Inmovilizado (stock * costo)
        top_insumos = sorted(insumos, key=lambda x: x.stock_actual * x.costo_unitario, reverse=True)[:5]
        context['chart_insumos_labels'] = json.dumps([i.nombre for i in top_insumos])
        # Convertimos a float para que Javascript/Chart.js pueda leer los Decimales de Python
        context['chart_insumos_data'] = json.dumps([float(i.stock_actual * i.costo_unitario) for i in top_insumos])

        # 4. Gráfico 2: Top 5 Productos con Mejor Margen de Ganancia
        top_recetas = sorted(recetas, key=lambda x: x.margen_ganancia, reverse=True)[:5]
        context['chart_recetas_labels'] = json.dumps([r.nombre_producto for r in top_recetas])
        context['chart_recetas_data'] = json.dumps([float(r.margen_ganancia) for r in top_recetas])
        recetas_brecha = sorted(recetas, key=lambda x: x.precio_venta, reverse=True)[:8]
        context['chart_brecha_labels'] = json.dumps([r.nombre_producto for r in recetas_brecha])
        context['chart_brecha_precio'] = json.dumps([float(r.precio_venta) for r in recetas_brecha])
        context['chart_brecha_costo'] = json.dumps([float(r.costo_total_produccion) for r in recetas_brecha])

        # Enviar KPIs a la vista
        context['kpi_valor_total'] = valor_total_bodega
        context['kpi_alertas'] = alertas_stock
        context['kpi_recetas'] = len(recetas)

        return context
    
def dashboard(request):
    # Aquí luego inyectaremos los datos de Chart.js y los totales del Kardex
    return render(request, 'inventory/dashboard.html')



class InsumoListView(LoginRequiredMixin, ListView):
    model = Insumo
    template_name = 'inventory/insumo_list.html'
    context_object_name = 'insumos'
    # Ordenamos alfabéticamente para que sea fácil de buscar
    ordering = ['nombre']



class InsumoCreateView(LoginRequiredMixin, CreateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'inventory/insumo_form.html'
    success_url = reverse_lazy('insumo_list')

    def form_valid(self, form):
        # Guardamos el insumo primero
        response = super().form_valid(form)
        
        # KARDEX: Si lo crearon con stock > 0, registramos la entrada inicial
        if self.object.stock_actual > 0:
            MovimientoStock.objects.create(
                insumo=self.object,
                tipo='entrada',
                cantidad=self.object.stock_actual,
                usuario=self.request.user,
                observacion="Inventario Inicial (Creación de Insumo)"
            )
        return response


class InsumoUpdateView(LoginRequiredMixin, UpdateView):
    model = Insumo
    form_class = InsumoForm
    template_name = 'inventory/insumo_form.html'
    success_url = reverse_lazy('insumo_list')

    def form_valid(self, form):
        # Obtenemos el insumo ANTES de que se guarde para ver cuánto stock tenía
        insumo_original = Insumo.objects.get(pk=self.kwargs['pk'])
        stock_anterior = insumo_original.stock_actual
        stock_nuevo = form.cleaned_data['stock_actual']
        diferencia = stock_nuevo - stock_anterior
        
        response = super().form_valid(form)
        
        # KARDEX: Si modificaron el stock a mano, guardamos la evidencia
        if diferencia != 0:
            tipo_mov = 'entrada' if diferencia > 0 else 'salida'
            MovimientoStock.objects.create(
                insumo=self.object,
                tipo=tipo_mov,
                cantidad=abs(diferencia),
                usuario=self.request.user,
                observacion=f"Ajuste manual de stock (Antes: {stock_anterior})"
            )
        return response


class InsumoDeleteView(LoginRequiredMixin, DeleteView):
    model = Insumo
    template_name = 'inventory/insumo_confirm_delete.html'
    success_url = reverse_lazy('insumo_list')




class KardexListView(LoginRequiredMixin, ListView):
    model = MovimientoStock
    template_name = 'inventory/kardex_list.html'
    context_object_name = 'movimientos'
    paginate_by = 100 # Mostramos de a 100 registros para no saturar la página

    def get_queryset(self):
        # Traemos los movimientos más recientes primero y optimizamos la consulta
        return MovimientoStock.objects.select_related('insumo', 'usuario').order_by('-fecha')



class RecetaListView(LoginRequiredMixin, ListView):
    model = Receta
    template_name = 'inventory/receta_list.html'
    context_object_name = 'recetas'

    def get_queryset(self):
        # MAGIA SENIOR: Le decimos a PostgreSQL que calcule el costo y el margen ANTES de enviarnos los datos.
        return Receta.objects.annotate(
            costo_bd=Coalesce(
                Sum(
                    F('ingredientereceta__cantidad_necesaria') * F('ingredientereceta__insumo__costo_unitario'),
                    output_field=DecimalField()
                ),
                Decimal('0.00'),
                output_field=DecimalField()
            )
        ).annotate(
            margen_bd=F('precio_venta') - F('costo_bd')
        ).order_by('nombre_producto')
    
class RecetaDetailView(LoginRequiredMixin, DetailView):
    model = Receta
    template_name = 'inventory/receta_detalle.html'
    context_object_name = 'receta'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_ingrediente'] = IngredienteRecetaForm()
        context['ingredientes'] = IngredienteReceta.objects.filter(receta=self.object).select_related('insumo')
        return context

@login_required
def agregar_ingrediente(request, receta_id):
    receta = get_object_or_404(Receta, pk=receta_id)
    if request.method == 'POST':
        form = IngredienteRecetaForm(request.POST)
        if form.is_valid():
            ingrediente = form.save(commit=False)
            ingrediente.receta = receta
            
            existente = IngredienteReceta.objects.filter(receta=receta, insumo=ingrediente.insumo).first()
            if existente:
                existente.cantidad_necesaria = ingrediente.cantidad_necesaria
                existente.save()
            else:
                ingrediente.save()
    return redirect('receta_detalle', pk=receta.id)

@login_required
def eliminar_ingrediente(request, ingrediente_id):
    ingrediente = get_object_or_404(IngredienteReceta, pk=ingrediente_id)
    receta_id = ingrediente.receta.id
    ingrediente.delete()
    return redirect('receta_detalle', pk=receta_id)





class SincronizarVentasView(LoginRequiredMixin, FormView):
    template_name = 'inventory/sincronizar_ventas.html'
    form_class = SincronizacionFudoForm
    success_url = reverse_lazy('sincronizar_ventas')

    def form_valid(self, form):
        archivo = self.request.FILES['archivo_ventas']
        
        # 1. LEER EL ARCHIVO (Soporta Excel y CSV blindado contra bytes)
        try:
            if archivo.name.endswith('.csv'):
                # Leemos los bytes de Django, los pasamos a texto y usamos StringIO para Pandas
                archivo_decodificado = archivo.read().decode('utf-8-sig', errors='replace')
                df = pd.read_csv(io.StringIO(archivo_decodificado), sep=None, engine='python')
            else:
                df = pd.read_excel(archivo)
        except Exception as e:
            messages.error(self.request, f"Error al leer el archivo: {str(e)}")
            return self.form_invalid(form)

        df.columns = df.columns.str.lower().str.strip()
        col_nombre = next((col for col in df.columns if 'producto' in col or 'nombre' in col or 'artículo' in col), None)
        col_cantidad = next((col for col in df.columns if 'cantidad' in col or 'cant' in col or 'unidades' in col), None)

        if not col_nombre or not col_cantidad:
            messages.error(self.request, "El archivo no es válido. Debe contener al menos una columna de 'Producto' y una de 'Cantidad'.")
            return self.form_invalid(form)

        df[col_cantidad] = pd.to_numeric(df[col_cantidad], errors='coerce').fillna(0)
        ventas_agrupadas = df.groupby(col_nombre)[col_cantidad].sum().reset_index()

        # 4. INTELIGENCIA DE TEXTO (BLINDADA CONTRA FALSOS POSITIVOS)
        # Creamos un diccionario para búsquedas exactas ignorando mayúsculas
        nombres_bd_exactos = {nombre.lower(): nombre for nombre in Receta.objects.values_list('nombre_producto', flat=True)}
        lista_nombres_bd = list(nombres_bd_exactos.values())
        
        resultados_preview = []
        for index, row in ventas_agrupadas.iterrows():
            nombre_fudo = str(row[col_nombre]).strip()
            cantidad_vendida = float(row[col_cantidad])

            if cantidad_vendida <= 0 or not nombre_fudo or str(nombre_fudo).lower() == 'nan':
                continue 

            nombre_fudo_lower = nombre_fudo.lower()

            # INTENTO 1: MATCH EXACTO (El más seguro)
            if nombre_fudo_lower in nombres_bd_exactos:
                receta = Receta.objects.get(nombre_producto=nombres_bd_exactos[nombre_fudo_lower])
                resultados_preview.append({
                    'nombre_fudo': nombre_fudo,
                    'nombre_bd': receta.nombre_producto,
                    'receta_id': receta.id,
                    'cantidad': cantidad_vendida,
                    'similitud': 100,
                    'estado': 'match'
                })
                continue

            # INTENTO 2: FUZZY MATCHING (Solo para faltas de ortografía muy menores)
            # Usamos fuzz.ratio que es sensible a las longitudes de las palabras
            mejor_match, score = process.extractOne(nombre_fudo, lista_nombres_bd)

            # Exigimos un 90% para evitar cruzar Capuccino con Capuccino Vienés
            if score >= 90:
                receta = Receta.objects.get(nombre_producto=mejor_match)
                resultados_preview.append({
                    'nombre_fudo': nombre_fudo,
                    'nombre_bd': receta.nombre_producto,
                    'receta_id': receta.id,
                    'cantidad': cantidad_vendida,
                    'similitud': score,
                    'estado': 'match'
                })
            else:
                resultados_preview.append({
                    'nombre_fudo': nombre_fudo,
                    'nombre_bd': 'No encontrado en BD',
                    'receta_id': None,
                    'cantidad': cantidad_vendida,
                    'similitud': score,
                    'estado': 'error'
                })

        # 5. GUARDAR EL BORRADOR
        self.request.session['preview_ventas'] = resultados_preview
        return redirect('sincronizar_confirmar')
    



class SincronizarConfirmarView(LoginRequiredMixin, View):
    template_name = 'inventory/sincronizar_confirmar.html'

    def get(self, request):
        preview_ventas = request.session.get('preview_ventas', [])
        if not preview_ventas:
            messages.warning(request, "No hay datos pendientes para sincronizar.")
            return redirect('sincronizar_ventas')

        insumos_a_descontar = {}
        for item in preview_ventas:
            if item['estado'] == 'match':
                receta = Receta.objects.get(id=item['receta_id'])
                
                # Forzamos la cantidad vendida a Decimal exacto
                cantidad_vendida = Decimal(str(item['cantidad'])).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                
                for ing in receta.ingredientereceta_set.select_related('insumo').all():
                    key = ing.insumo.id
                    cantidad_ingrediente = Decimal(str(ing.cantidad_necesaria))
                    
                    # Matemática blindada a 3 decimales
                    qty = (cantidad_ingrediente * cantidad_vendida).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                    
                    if key in insumos_a_descontar:
                        insumos_a_descontar[key]['cantidad_total'] += qty
                    else:
                        insumos_a_descontar[key] = {
                            'nombre': ing.insumo.nombre,
                            'cantidad_total': qty,
                            'unidad': ing.insumo.unidad_medida,
                            'stock_actual': Decimal(str(ing.insumo.stock_actual))
                        }

        context = {
            'ventas': preview_ventas,
            'insumos_proyectados': insumos_a_descontar.values()
        }
        return render(request, self.template_name, context)

    def post(self, request):
        preview_ventas = request.session.get('preview_ventas', [])
        if not preview_ventas:
            return redirect('sincronizar_ventas')

        try:
            with transaction.atomic():
                descuentos_totales = {}
                for item in preview_ventas:
                    if item['estado'] == 'match':
                        receta = Receta.objects.get(id=item['receta_id'])
                        cantidad_vendida = Decimal(str(item['cantidad'])).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                        
                        for ing in receta.ingredientereceta_set.all():
                            cantidad_ingrediente = Decimal(str(ing.cantidad_necesaria))
                            cantidad_gasto = (cantidad_ingrediente * cantidad_vendida).quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)
                            
                            if ing.insumo in descuentos_totales:
                                descuentos_totales[ing.insumo] += cantidad_gasto
                            else:
                                descuentos_totales[ing.insumo] = cantidad_gasto

                for insumo, total_descuento in descuentos_totales.items():
                    insumo.stock_actual -= total_descuento
                    insumo.save()

                    MovimientoStock.objects.create(
                        insumo=insumo,
                        tipo='salida',
                        cantidad=total_descuento,
                        usuario=request.user,
                        observacion="Descuento automático (Sincronización Fudo)"
                    )

            del request.session['preview_ventas']
            messages.success(request, "¡Sincronización exitosa! La bodega y el Kardex han sido actualizados con exactitud.")
            return redirect('kardex_list')

        except Exception as e:
            messages.error(request, f"Se detuvo la sincronización para proteger los datos. Error: {str(e)}")
            return redirect('sincronizar_confirmar')
        




@login_required
def actualizar_precio_receta(request, receta_id):
    receta = get_object_or_404(Receta, pk=receta_id)
    if request.method == 'POST':
        form = RecetaPrecioForm(request.POST, instance=receta)
        if form.is_valid():
            form.save()
            messages.success(request, f"¡Precio de {receta.nombre_producto} actualizado con éxito!")
    return redirect('receta_detalle', pk=receta.id)
