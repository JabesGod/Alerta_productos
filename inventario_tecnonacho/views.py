from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from .models import Producto
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.contrib.auth import logout
from .forms import CustomUserCreationForm
from django.db.models import Q
from django.http import JsonResponse
import json
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator

def iniciar_sesion(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('lista_productos')  
        return render(request, 'inicio.html', {'form': form, 'error': 'Usuario o contraseña incorrectos'})
    else:
        form = AuthenticationForm()
    return render(request, 'inicio.html', {'form': form})

def registrar_usuario(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('iniciar_sesion') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'registro.html', {'form': form})


@login_required
def salir(request):
    logout(request)
    return redirect('iniciar_sesion')



@login_required
def lista_productos(request):
    # Verificar si la tabla existe en la base de datos
    table_name = 'inventario_tecnonacho_producto'
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", [table_name])
        table_exists = cursor.fetchone()

    if not table_exists:
        # Si la tabla no existe, retornamos una lista vacía
        productos = Producto.objects.none()
    else:
        # Obtener productos según si el usuario es superusuario
        if request.user.is_superuser:
            productos = Producto.objects.all()
        else:
            productos = Producto.objects.filter(user=request.user)

        # Filtrar productos según la búsqueda (si se ingresó un query)
        query = request.GET.get('q', '').strip()
        if query:
            productos = productos.filter(
                Q(sku__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(user__username__icontains=query) |
                Q(precio_compra__icontains=query) |
                Q(proveedor__icontains=query)
            )

        # Ordenar productos según el criterio solicitado
        ordenar_por = request.GET.get('ordenar_por', 'id')
        orden = request.GET.get('orden', 'asc')
        if orden == 'desc':
            ordenar_por = f'-{ordenar_por}'
        productos = productos.order_by(ordenar_por)

    # *** Aquí agregamos el paginador ***
    paginator = Paginator(productos, 10)  # Dividir productos en páginas de 20
    page_number = request.GET.get('page')  # Número de página actual desde los parámetros
    productos_paginados = paginator.get_page(page_number)  # Productos de la página actual

    # Renderizar la plantilla con los datos
    return render(request, 'lista_productos.html', {
        'productos': productos_paginados,  # Pasar productos paginados a la plantilla
        'niveles_importancia': range(1, 6),
    })

@csrf_exempt
def toggle_listo(request, pk):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        data = json.loads(request.body)
        producto.listo = data.get('listo', False)
        producto.save()
        return JsonResponse({'success': True, 'listo': producto.listo})
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

@login_required
def agregar_producto(request):
    if request.method == 'POST':
        sku = request.POST.get('sku')
        descripcion = request.POST.get('descripcion')
        importancia = request.POST.get('importancia')
        user = request.user

        try:
            Producto.objects.create(
                sku=sku,
                descripcion=descripcion,
                importancia=importancia,
                user=user
            )
        except IntegrityError:
            error_message = "El SKU ya existe."
            return render(request, 'lista_productos.html', {'error': error_message})

        return redirect('lista_productos') 

    return render(request, 'lista_productos.html')  


@login_required
def actualizar_producto(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        # Verificar si el usuario es superusuario para permitir editar el SKU, proveedor y nota
        if request.user.is_superuser:
            producto.sku = request.POST.get('sku')
            producto.proveedor = request.POST.get('proveedor')  # Solo editable por admin
            producto.nota = request.POST.get('nota')  # Solo editable por admin
        else:
            # Si no es superusuario, prohíbe modificar estos campos
            if request.POST.get('sku') != producto.sku or request.POST.get('proveedor') or request.POST.get('nota'):
                return HttpResponseForbidden("No tienes permiso para modificar estos campos.")

        # Actualizar los demás campos (disponibles para todos los usuarios)
        producto.descripcion = request.POST.get('descripcion')
        producto.precio_compra = request.POST.get('precio_compra')
        producto.importancia = request.POST.get('importancia')

        # Guardar cambios
        producto.save()
        return redirect('lista_productos')

    return redirect('lista_productos')

@login_required
def eliminar_producto(request, producto_id):
    if not request.user.is_superuser:
        return JsonResponse({'success': False, 'message': 'No tienes permisos para realizar esta acción.'}, status=403)
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        producto.delete()
        return JsonResponse({'success': True, 'message': 'Producto eliminado correctamente.'})
    except Producto.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Producto no encontrado.'}, status=404)