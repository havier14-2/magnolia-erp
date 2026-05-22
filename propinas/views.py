from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum

# Importamos los 3 Modelos
from .models import ReglaDistribucion, Turno, ParticipanteTurno

# Importamos los 3 Formularios
from .forms import ReglaDistribucionForm, TurnoForm, ParticipanteForm

# Mixin de seguridad (Reutilizado)
class SoloAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Administrador').exists()

# 1. LISTAR REGLAS Y CALCULAR TOTALES
class ReglaListView(LoginRequiredMixin, SoloAdminMixin, ListView):
    model = ReglaDistribucion
    template_name = 'propinas/regla_list.html'
    context_object_name = 'reglas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculamos la suma total de los porcentajes activos
        totales = ReglaDistribucion.objects.filter(activo=True).aggregate(
            total_am=Sum('porcentaje_am'),
            total_pm=Sum('porcentaje_pm')
        )
        context['total_am'] = totales['total_am'] or 0
        context['total_pm'] = totales['total_pm'] or 0
        return context

# 2. CREAR REGLA
class ReglaCreateView(LoginRequiredMixin, SoloAdminMixin, CreateView):
    model = ReglaDistribucion
    form_class = ReglaDistribucionForm
    template_name = 'propinas/regla_form.html'
    success_url = reverse_lazy('reglas_lista')

# 3. EDITAR REGLA
class ReglaUpdateView(LoginRequiredMixin, SoloAdminMixin, UpdateView):
    model = ReglaDistribucion
    form_class = ReglaDistribucionForm
    template_name = 'propinas/regla_form.html'
    success_url = reverse_lazy('reglas_lista')

# 4. ELIMINAR REGLA
class ReglaDeleteView(LoginRequiredMixin, SoloAdminMixin, DeleteView):
    model = ReglaDistribucion
    template_name = 'propinas/regla_confirmar_borrado.html'
    success_url = reverse_lazy('reglas_lista')


def calcular_reparto_turno(turno):
    """
    Toma un turno y reparte el pozo entre los participantes 
    basándose en las reglas de porcentaje configuradas.
    """
    participantes = turno.participantes.all()
    if not participantes:
        return

    pozo_total = turno.total_pozo
    tipo_turno = turno.tipo # 'AM' o 'PM'

    # 1. Agrupar participantes por rol para dividir el pozo del área
    # Ej: Si hay 2 Garzones, el 60% se divide entre 2.
    roles_en_turno = participantes.values('rol').distinct()

    for item in roles_en_turno:
        rol_id = item['rol']
        regla = ReglaDistribucion.objects.get(pk=rol_id)
        
        # Obtener el % según el turno
        porcentaje = regla.porcentaje_am if tipo_turno == 'AM' else regla.porcentaje_pm
        
        # Calcular cuánto le toca a esta área (Cocina, Barra, etc.)
        monto_area = (pozo_total * porcentaje) / 100
        
        # ¿Cuántas personas hay en este rol hoy?
        personas_en_rol = participantes.filter(rol_id=rol_id)
        cantidad_personas = personas_en_rol.count()
        
        if cantidad_personas > 0:
            monto_por_persona = int(monto_area / cantidad_personas)
            # Actualizar a cada persona en la base de datos
            personas_en_rol.update(monto_asignado=monto_por_persona)
    


class TurnoCreateView(LoginRequiredMixin, SoloAdminMixin, CreateView):
    model = Turno
    form_class = TurnoForm
    template_name = 'propinas/turno_form.html'
    
    def get_success_url(self):
        return reverse_lazy('turno_detalle', kwargs={'pk': self.object.pk})

class TurnoDetailView(LoginRequiredMixin, SoloAdminMixin, DetailView):
    model = Turno
    template_name = 'propinas/turno_detalle.html'
    context_object_name = 'turno'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_participante'] = ParticipanteForm()
        # Calculamos el reparto antes de mostrar la página
        calcular_reparto_turno(self.object)
        return context

# Vista para procesar la adición de un empleado
def agregar_participante(request, turno_id):
    turno = get_object_or_404(Turno, pk=turno_id)
    if request.method == 'POST':
        form = ParticipanteForm(request.POST)
        if form.is_valid():
            participante = form.save(commit=False)
            participante.turno = turno
            participante.save()
            # Recalcular automáticamente al añadir a alguien
            calcular_reparto_turno(turno)
    return redirect('turno_detalle', pk=turno_id)

def eliminar_participante(request, participante_id):
    participante = get_object_or_404(ParticipanteTurno, pk=participante_id)
    turno_id = participante.turno.id
    participante.delete()
    # Recalcular automáticamente al quitar a alguien
    calcular_reparto_turno(get_object_or_404(Turno, pk=turno_id))
    return redirect('turno_detalle', pk=turno_id)
