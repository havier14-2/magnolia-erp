from django.urls import path
from . import views

urlpatterns = [
    path('', views.UsuarioListView.as_view(), name='usuarios_lista'),
    path('crear/', views.UsuarioCreateView.as_view(), name='usuario_crear'),
    path('editar/<int:pk>/', views.UsuarioUpdateView.as_view(), name='usuario_editar'),
    path('eliminar/<int:pk>/', views.UsuarioDeleteView.as_view(), name='usuario_eliminar'),
]