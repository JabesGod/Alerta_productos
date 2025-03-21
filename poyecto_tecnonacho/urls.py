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
    path('notificaciones/obtener/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('notificaciones/marcar_leidas/', views.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
    path('notificaciones/eliminar/<int:notificacion_id>/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('notificaciones/eliminar_todas/', views.eliminar_todas_notificaciones, name='eliminar_todas_notificaciones'),
    path('usuarios/cambiar-rol/<int:user_id>/', views.cambiar_rol_usuario, name='cambiar_rol_usuario'),
    path('proveedores/', views.lista_proveedores, name='lista_proveedores'),
    path('proveedores/agregar/', views.agregar_proveedor, name='agregar_proveedor'),
    path('proveedores/editar/<int:proveedor_id>/', views.editar_proveedor, name='editar_proveedor'),
    path('proveedores/eliminar/<int:proveedor_id>/', views.eliminar_proveedor, name='eliminar_proveedor'),
    path('obtener-ciudades/', views.obtener_ciudades, name='obtener_ciudades'),
    path('categorias/', views.lista_categorias, name='lista_categorias'),
    path('categorias/agregar/', views.agregar_categoria, name='agregar_categoria'),
    path('editar_categoria/<int:id>/', views.editar_categoria, name='editar_categoria'),
    path('eliminar_categoria/<int:categoria_id>/', views.eliminar_categoria, name='eliminar_categoria'),
    path('marcas/', views.lista_marcas, name='lista_marcas'),
    path('marcas/agregar/', views.agregar_marca, name='agregar_marca'),
    path('marcas/editar/<int:id>/', views.editar_marca, name='editar_marca'),
    path('marcas/eliminar/<int:id>/', views.eliminar_marca, name='eliminar_marca'),
    path('verificar_sku/', views.verificar_sku_existente, name='verificar_sku_existente'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)