from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('insumos/', views.InsumoListView.as_view(), name='insumo_list'),
    path('insumos/', views.InsumoListView.as_view(), name='insumo_list'),
    path('insumos/nuevo/', views.InsumoCreateView.as_view(), name='insumo_crear'),
    path('insumos/editar/<int:pk>/', views.InsumoUpdateView.as_view(), name='insumo_editar'),
    path('insumos/eliminar/<int:pk>/', views.InsumoDeleteView.as_view(), name='insumo_eliminar'),
    path('kardex/', views.KardexListView.as_view(), name='kardex_list'),
    path('recetas/', views.RecetaListView.as_view(), name='receta_list'),
    path('recetas/<int:pk>/', views.RecetaDetailView.as_view(), name='receta_detalle'),
    path('recetas/<int:receta_id>/agregar/', views.agregar_ingrediente, name='agregar_ingrediente'),
    path('recetas/ingrediente/eliminar/<int:ingrediente_id>/', views.eliminar_ingrediente, name='eliminar_ingrediente'),
    path('sincronizar/', views.SincronizarVentasView.as_view(), name='sincronizar_ventas'),
    path('sincronizar/confirmar/', views.SincronizarConfirmarView.as_view(), name='sincronizar_confirmar'),
    # Añade esto junto a las rutas de escandallos
    path('recetas/<int:receta_id>/actualizar-precio/', views.actualizar_precio_receta, name='actualizar_precio_receta'),

]