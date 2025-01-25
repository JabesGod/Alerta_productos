from django.urls import path
from inventario_tecnonacho import views

urlpatterns = [
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registrar_usuario, name='registrar_usuario'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('agregar_producto/', views.agregar_producto, name='agregar_producto'),
    path('eliminar_producto/', views.eliminar_producto, name='eliminar_producto'),
    path('salir/', views.salir, name='salir'),
    path('producto/actualizar/<int:producto_id>/', views.actualizar_producto, name='actualizar_producto'),
    path('producto/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/toggle_listo/<int:pk>/', views.toggle_listo, name='toggle_listo'),

]