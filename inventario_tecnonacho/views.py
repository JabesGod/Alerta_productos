from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, connection
from django.db.models import Q
import json
from .models import Producto
from .forms import CustomUserCreationForm, CambiarContraseñaForm, FotoPerfilForm
User = get_user_model()



def es_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(es_admin)
def lista_usuarios(request):
    usuarios = User.objects.all()
    return render(request, "lista_usuarios.html", {"usuarios": usuarios})

@login_required
@user_passes_test(es_admin)
def eliminar_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)
    if usuario.is_superuser:
        messages.error(request, "No puedes eliminar a otro administrador.")
    else:
        usuario.delete()
        messages.success(request, "Usuario eliminado con éxito.")
    return redirect("lista_usuarios")

@login_required
@user_passes_test(es_admin)
def cambiar_contraseña_usuario(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        form = SetPasswordForm(usuario, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Contraseña cambiada con éxito.")
            return redirect("lista_usuarios")
    else:
        form = SetPasswordForm(usuario)

    return render(request, "cambiar_contraseña_usuario.html", {"form": form, "usuario": usuario})

@login_required
def perfil_usuario(request):
    if request.method == "POST":
        if "cambiar_contraseña" in request.POST:
            form_contraseña = CambiarContraseñaForm(user=request.user, data=request.POST)
            if form_contraseña.is_valid():
                form_contraseña.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña cambiada con éxito.")
                return redirect("perfil_usuario")
            else:
                messages.error(request, "Error al cambiar la contraseña.")

        elif "actualizar_foto" in request.POST:
            form_foto = FotoPerfilForm(request.POST, request.FILES, instance=request.user)
            if form_foto.is_valid():
                form_foto.save()
                messages.success(request, "Foto de perfil actualizada con éxito.")
                return redirect("perfil_usuario")
            else:
                messages.error(request, "Error al actualizar la foto de perfil.")

        elif "eliminar_foto" in request.POST:
            request.user.foto_perfil.delete(save=True)
            messages.success(request, "Foto de perfil eliminada con éxito.")
            return redirect("perfil_usuario")

    else:
        form_contraseña = CambiarContraseñaForm(user=request.user)
        form_foto = FotoPerfilForm(instance=request.user)

    return render(request, "perfil.html", {
        "form_contraseña": form_contraseña,
        "form_foto": form_foto,
    })






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
