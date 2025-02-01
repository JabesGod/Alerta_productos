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
from django.contrib import messages
import json
from django.db import connection
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseForbidden
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError

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
    table_name = 'inventario_tecnonacho_producto'
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", [table_name])
        table_exists = cursor.fetchone()

    if not table_exists:
        productos = Producto.objects.none()
        total_listos = 0
        total_no_listos = 0
        importancia_contadores = {str(i): 0 for i in range(1, 6)}  # Inicializa contadores en 0
    else:
        if request.user.is_superuser:
            productos = Producto.objects.all()
        else:
            productos = Producto.objects.filter(user=request.user)

        # Búsqueda
        query = request.GET.get('q', '').strip()
        if query:
            productos = productos.filter(
                Q(sku__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(user__username__icontains=query) |
                Q(precio_compra__icontains=query) |
                Q(proveedor__icontains=query)
            )

        # Ordenación
        ordenar_por = request.GET.get('ordenar_por', 'id')
        orden = request.GET.get('orden', 'asc')
        if orden == 'desc':
            ordenar_por = f'-{ordenar_por}'
        productos = productos.order_by(ordenar_por)

        # Contadores
        total_listos = productos.filter(listo=True).count()
        total_no_listos = productos.filter(listo=False).count()
        importancia_contadores = {
            "1": productos.filter(importancia=1).count(),
            "2": productos.filter(importancia=2).count(),
            "3": productos.filter(importancia=3).count(),
            "4": productos.filter(importancia=4).count(),
            "5": productos.filter(importancia=5).count(),
        }

        # Agregar nuevo producto si es POST
        if request.method == 'POST':
            sku = request.POST.get('sku')
            descripcion = request.POST.get('descripcion')
            importancia = request.POST.get('importancia')

            producto_existente = Producto.objects.filter(sku=sku).first()

            if producto_existente:
                if not producto_existente.listo:
                    messages.error(request, "El SKU ya existe y no está marcado como listo. No se puede agregar.")
                else:
                    Producto.objects.create(
                        sku=sku,
                        descripcion=descripcion,
                        importancia=importancia,
                        user=request.user
                    )
                    messages.success(request, "Producto duplicado agregado exitosamente porque `listo` está activo.")
            else:
                Producto.objects.create(
                    sku=sku,
                    descripcion=descripcion,
                    importancia=importancia,
                    user=request.user
                )
                messages.success(request, "Producto agregado exitosamente.")

    # Paginación
    paginator = Paginator(productos, 15)
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)

    return render(request, 'lista_productos.html', {
        'productos': productos_paginados,
        'niveles_importancia': range(1, 6),
        'query': query,
        'ordenar_por': ordenar_por.strip('-'),
        'orden': orden,
        'total_listos': total_listos,
        'total_no_listos': total_no_listos,
        'importancia_contadores': importancia_contadores,
    })





@csrf_exempt
def toggle_listo(request, pk):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)
        data = json.loads(request.body)

        nuevo_estado = data.get('listo', False)
        producto.listo = nuevo_estado
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

        producto_existente = Producto.objects.filter(sku=sku).first()

        if producto_existente:
            if not producto_existente.listo:
                messages.error(request, "El SKU ya existe pero no está marcado como listo.")
            else:
                Producto.objects.create(
                    sku=sku,
                    descripcion=descripcion,
                    importancia=importancia,
                    user=user
                )
                messages.success(request, "Producto duplicado agregado exitosamente porque `listo` está activo.")
        else:
            try:
                Producto.objects.create(
                    sku=sku,
                    descripcion=descripcion,
                    importancia=importancia,
                    user=user
                )
                messages.success(request, "Producto agregado exitosamente.")
            except IntegrityError:
                messages.error(request, "Error al agregar el producto.")

        return redirect('/lista_productos?agregar=1')  # Agrega `?agregar=1` para abrir el modal

    return redirect('lista_productos')



def validar_sku_unico(value):
    producto_existente = Producto.objects.filter(sku=value).first()
    if producto_existente and not producto_existente.listo:
        raise ValidationError("El SKU ya existe y no está marcado como listo.")


@login_required
def actualizar_producto(request, producto_id):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, id=producto_id)

        if request.user.is_superuser:
            producto.sku = request.POST.get('sku')
            producto.proveedor = request.POST.get('proveedor')
            producto.nota = request.POST.get('nota')  
        else:
        
            if request.POST.get('sku') != producto.sku or request.POST.get('proveedor') or request.POST.get('nota'):
                return HttpResponseForbidden("No tienes permiso para modificar estos campos.")

        producto.descripcion = request.POST.get('descripcion')
        producto.precio_compra = request.POST.get('precio_compra')
        producto.importancia = request.POST.get('importancia')

   
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
    

import pandas as pd
import os
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

def cargar_sku_desde_excel():
    """Lee el archivo Excel y devuelve un diccionario con los SKU y descripciones."""
    ruta_excel = os.path.join(settings.BASE_DIR, 'actualizada.xlsx')

    try:
        df = pd.read_excel(ruta_excel, dtype={'CódigoInventario': str})
        df.fillna("", inplace=True)  # Rellenar NaN con cadenas vacías
        
        # Convertir en diccionario { SKU: Descripción }
        return dict(zip(df['CódigoInventario'], df['Descripcion']))
    except Exception as e:
        print(f"Error al leer el archivo Excel: {e}")
        return {}

@csrf_exempt
def obtener_descripcion_sku(request):
    """Recibe un SKU y devuelve la descripción desde el archivo Excel."""
    if request.method == "POST":
        sku = request.POST.get('sku', '').strip()
        datos_excel = cargar_sku_desde_excel()
        
        descripcion = datos_excel.get(sku, "No encontrado")

        return JsonResponse({"descripcion": descripcion})

    return JsonResponse({"error": "Método no permitido"}, status=400)
