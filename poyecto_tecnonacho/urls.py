from django.urls import path
from inventario_tecnonacho import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.iniciar_sesion, name='iniciar_sesion'),
    path('registro/', views.registrar_usuario, name='registrar_usuario'),
    path('lista_productos/', views.lista_productos, name='lista_productos'),
    path('agregar_producto/', views.agregar_producto, name='agregar_producto'),
    path('salir/', views.salir, name='salir'),
    path('producto/actualizar/<int:producto_id>/', views.actualizar_producto, name='actualizar_producto'),
    path('producto/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('producto/toggle_listo/<int:pk>/', views.toggle_listo, name='toggle_listo'),
    path('obtener_descripcion_sku/', views.obtener_descripcion_sku, name='obtener_descripcion_sku'),
    path("perfil/", views.perfil_usuario, name="perfil_usuario"),
    path("usuarios/", views.lista_usuarios, name="lista_usuarios"),
    path("usuarios/eliminar/<int:user_id>/", views.eliminar_usuario, name="eliminar_usuario"),
    path("usuarios/cambiar_contraseña/<int:user_id>/", views.cambiar_contraseña_usuario, name="cambiar_contraseña_usuario"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)