from django.urls import path
from . import views

urlpatterns = [
    path('configuracion/', views.ReglaListView.as_view(), name='reglas_lista'),
    path('configuracion/crear/', views.ReglaCreateView.as_view(), name='regla_crear'),
    path('configuracion/editar/<int:pk>/', views.ReglaUpdateView.as_view(), name='regla_editar'),
    path('configuracion/eliminar/<int:pk>/', views.ReglaDeleteView.as_view(), name='regla_eliminar'),

    path('diario/', views.TurnoCreateView.as_view(), name='turno_crear'),
    path('diario/<int:pk>/', views.TurnoDetailView.as_view(), name='turno_detalle'),
    path('diario/agregar/<int:turno_id>/', views.agregar_participante, name='agregar_participante'),
    path('participante/eliminar/<int:participante_id>/', views.eliminar_participante, name='eliminar_participante'),

]