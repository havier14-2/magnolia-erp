from django.shortcuts import render, redirect

# Create your views here. USerssss

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import CreacionUsuarioForm

# Mixin de seguridad: Solo permite el acceso si el usuario es Administrador o Superusuario
class SoloAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Administrador').exists()

# 1. READ: Listar Usuarios
class UsuarioListView(LoginRequiredMixin, SoloAdminMixin, ListView):
    model = User
    template_name = 'users/usuario_list.html'
    context_object_name = 'usuarios'
    
    def get_queryset(self):
        # Excluimos superuser Y a los inactivos (despedidos/eliminados)
        return User.objects.filter(is_active=True).exclude(is_superuser=True).prefetch_related('groups')

# 2. CREATE: Crear Usuario
class UsuarioCreateView(LoginRequiredMixin, SoloAdminMixin, CreateView):
    model = User
    form_class = CreacionUsuarioForm
    template_name = 'users/usuario_form.html'
    success_url = reverse_lazy('usuarios_lista') # A dónde redirigir al guardar con éxito


class UsuarioUpdateView(LoginRequiredMixin, SoloAdminMixin, UpdateView):
    model = User
    # Podríamos usar el mismo CreacionUsuarioForm, pero no queremos obligar 
    # a reescribir la contraseña cada vez que editamos el nombre. 
    # Para hacerlo rápido y profesional, definimos los campos aquí:
    fields = ['username', 'first_name', 'last_name', 'email']
    template_name = 'users/usuario_form.html' # Reutilizamos el mismo HTML de crear
    success_url = reverse_lazy('usuarios_lista')

    def get_context_data(self, **kwargs):
        # Le enviamos una variable extra al HTML para saber que estamos editando
        context = super().get_context_data(**kwargs)
        context['es_edicion'] = True
        return context

# 4. DELETE (Soft Delete): Desactivar Usuario
class UsuarioDeleteView(LoginRequiredMixin, SoloAdminMixin, DeleteView):
    model = User
    template_name = 'users/usuario_confirmar_borrado.html'
    success_url = reverse_lazy('usuarios_lista')

    # Sobrescribimos el método de borrado real para hacer un Soft Delete
    def form_valid(self, form):
        usuario = self.get_object()
        usuario.is_active = False
        usuario.save()
        return redirect(self.success_url)