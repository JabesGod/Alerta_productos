from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash, get_user_model
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.exceptions import ValidationError
from django.views.decorators.csrf import csrf_exempt
from django.db import IntegrityError, connection
from django.db.models import Q
import json
from .models import Producto
from .forms import CustomUserCreationForm, CambiarContraseñaForm, FotoPerfilForm
User = get_user_model()
from .models import UsuarioPersonalizado
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from .models import Proveedor
from .forms import ProveedorForm
from django.shortcuts import render
from .models import Proveedor, Marca, Categoria
from cities_light.models import Region, City
from .models import Categoria
from .forms import CategoriaForm

def es_admin(user):
    return user.is_superuser



@login_required
@user_passes_test(es_admin)
def lista_usuarios(request):
    query = request.GET.get('q', '')  # Capturamos el valor del buscador
    usuarios = UsuarioPersonalizado.objects.all().order_by('id')
    
    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) | 
            Q(first_name__icontains=query) | 
            Q(last_name__icontains=query) | 
            Q(email__icontains=query)
        )
    
    paginator = Paginator(usuarios, 15)
    page_number = request.GET.get('page')
    usuarios_paginados = paginator.get_page(page_number)
    
    return render(request, "lista_usuarios.html", {"usuarios": usuarios_paginados, "query": query})


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
    form_foto = None  # Inicialización previa
    form_contraseña = None  # También inicializamos form_contraseña

    if request.method == "POST":
        if "cambiar_contraseña" in request.POST:
            form_contraseña = CambiarContraseñaForm(user=request.user, data=request.POST)
            if form_contraseña.is_valid():
                form_contraseña.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña cambiada con éxito.")
                return redirect("perfil_usuario")
            else:
                messages.error(request, "Error al cambiar la contraseña, contraseña no valida")

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

    if form_contraseña is None:
        form_contraseña = CambiarContraseñaForm(user=request.user)
    if form_foto is None:
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
    """
    Vista que maneja la lista de productos con filtros, búsqueda, paginación y ordenación.
    """

    table_name = 'inventario_tecnonacho_producto'
    with connection.cursor() as cursor:
        cursor.execute("SHOW TABLES LIKE %s", [table_name])
        table_exists = cursor.fetchone()

    if not table_exists:
        productos = Producto.objects.none()
        total_listos = 0
        total_no_listos = 0
        importancia_contadores = {str(i): 0 for i in range(1, 6)}
    else:
        # 🔹 Obtener todos los productos según el usuario
        if request.user:
            productos = Producto.objects.all()
        else:
            productos = Producto.objects.filter(user=request.user)

        # 🔹 Filtro de categoría
        categoria_filtro = request.GET.get('categoria', '').strip()
        if categoria_filtro:
            productos = productos.filter(categoria=categoria_filtro)

        # 🔹 Filtro de importancia (nuevo filtro)
        importancia_filtro = request.GET.get('importancia')
        if importancia_filtro:
            productos = productos.filter(importancia=int(importancia_filtro))

        # 🔹 Filtro de estado "listo" (nuevo filtro)
        listo_filtro = request.GET.get('listo')
        if listo_filtro is not None:
            productos = productos.filter(listo=(listo_filtro.lower() == 'true'))

        # 🔹 Filtro de búsqueda
        query = request.GET.get('q', '').strip()
        if query:
            productos = productos.filter(
                Q(sku__icontains=query) |
                Q(descripcion__icontains=query) |
                Q(user__username__icontains=query) |
                Q(precio_compra__icontains=query) |
                Q(proveedor__icontains=query) |
                Q(nota__icontains=query)
            )

        # 🔹 Ordenación
        ordenar_por = request.GET.get('ordenar_por', '-id')
        orden = request.GET.get('orden', 'asc')
        if orden == 'desc':
            ordenar_por = f'-{ordenar_por}'
        productos = productos.order_by(ordenar_por)

        # 🔹 Contadores para los filtros
        total_listos = Producto.objects.filter(listo=True).count()
        total_no_listos = Producto.objects.filter(listo=False).count()
        importancia_contadores = {
            str(i): Producto.objects.filter(importancia=i).count() for i in range(1, 6)
        }

        # 🔹 Manejo de creación de productos
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

    # 🔹 Paginación (después de los filtros)
    paginator = Paginator(productos, 15)
    page_number = request.GET.get('page')
    productos_paginados = paginator.get_page(page_number)

    # 🔹 Obtener todos los parámetros de filtro actuales para mantenerlos en la paginación
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    filtro_url = query_params.urlencode()  # Convierte los parámetros en una cadena para la URL

    return render(request, 'lista_productos.html', {
        'productos': productos_paginados,
        'niveles_importancia': range(1, 6),
        'query': query,
        'categoria_filtro': categoria_filtro,
        'ordenar_por': ordenar_por.strip('-'),
        'orden': orden,
        'total_listos': total_listos,
        'total_no_listos': total_no_listos,
        'importancia_contadores': importancia_contadores,
        'filtro_url': filtro_url,  # 🔹 Pasamos los filtros a la plantilla
    })

@csrf_exempt
def toggle_listo(request, pk):
    if request.method == 'POST':
        producto = get_object_or_404(Producto, pk=pk)

        # Solo permitir cambios si el usuario es superuser
        if not request.user.is_superuser:
            return JsonResponse({'success': False, 'error': 'No tienes permisos para cambiar este estado'}, status=403)

        data = json.loads(request.body)
        nuevo_estado = data.get('listo', False)
        
        producto.listo = nuevo_estado

        # 🔹 Cambiar la categoría automáticamente
        if producto.listo:
            producto.categoria = 'realizados'  # ✅ Si se marca como listo, pasa a "Realizados"
        else:
            producto.categoria = 'faltantes'  # ✅ Si se desmarca, pasa a "Faltantes" (color rojo)

        producto.save()

        return JsonResponse({'success': True, 'listo': producto.listo, 'categoria': producto.get_categoria_display()})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

from .models import Producto, Notificacion
from django.contrib.auth import get_user_model
User = get_user_model()


@login_required
def agregar_producto(request):
    if request.method == 'POST':
        sku = request.POST.get('sku')
        descripcion = request.POST.get('descripcion')
        importancia = request.POST.get('importancia')
        cantidad = request.POST.get('cantidad')
        categoria = request.POST.get('categoria')
        user = request.user

        producto_existente = Producto.objects.filter(sku=sku).first()

        if producto_existente and not producto_existente.listo:
            messages.error(request, "El SKU ya existe pero no está marcado como listo.")
        else:
            nuevo_producto = Producto.objects.create(
                sku=sku,
                descripcion=descripcion,
                importancia=importancia,
                cantidad=cantidad,
                categoria=categoria,
                user=user
            )
            messages.success(request, "Producto agregado exitosamente.")

            # 🔔 Crear notificación para administradores
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notificacion.objects.create(
                    usuario=admin,
                    mensaje=f"Nuevo producto agregado: {nuevo_producto.descripcion} (SKU: {nuevo_producto.sku})"
                )

        return redirect('lista_productos')

    return redirect('lista_productos')


from django.http import JsonResponse
from .models import Producto
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt  # Para pruebas (mejor usar @csrf_protect con AJAX)
def verificar_sku_existente(request):
    if request.method == "POST":
        sku = request.POST.get("sku")
        id_producto = request.POST.get("id_producto")

        producto_existente = Producto.objects.filter(sku=sku).exclude(id=id_producto).exists()

        return JsonResponse({"duplicado": producto_existente})

    return JsonResponse({"error": "Método no permitido"}, status=400)



from django.utils.timezone import localtime

@login_required
def obtener_notificaciones(request):
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:5]

    data = {
        "notificaciones": [
            {
                "id": n.id,
                "mensaje": n.mensaje,
                "leido": n.leido,
                "fecha": localtime(n.fecha_creacion).strftime("%d/%m/%Y %I:%M %p"),
                "imagen_usuario": n.usuario.foto_perfil.url if n.usuario.foto_perfil else "/static/images/default.png",  # ✅ Ahora es la imagen del usuario que creó la notificación
            } for n in notificaciones
        ],
        "total_no_leidas": Notificacion.objects.filter(usuario=request.user, leido=False).count()
    }
    return JsonResponse(data)




@login_required
def marcar_notificaciones_leidas(request):
    Notificacion.objects.filter(usuario=request.user, leido=False).update(leido=True)
    return JsonResponse({"success": True})


@login_required
def eliminar_notificacion(request, notificacion_id):
    try:
        notificacion = Notificacion.objects.get(id=notificacion_id, usuario=request.user)
        notificacion.delete()
        return JsonResponse({"success": True})
    except Notificacion.DoesNotExist:
        return JsonResponse({"success": False, "error": "Notificación no encontrada."}, status=404)


@login_required
def eliminar_todas_notificaciones(request):

    Notificacion.objects.filter(usuario=request.user).delete()
    return JsonResponse({"success": True})

from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist

@receiver(pre_save, sender=Producto)
def notificar_cambio_producto(sender, instance, **kwargs):
    """ Crea una notificación cuando `listo` cambia a True o si se edita cualquier otro campo importante """
    try:
        producto_viejo = Producto.objects.get(pk=instance.pk)  # Obtener versión anterior del producto
    except Producto.DoesNotExist:
        return  # Si no existe, es un nuevo producto y no hacemos nada

    # Si `listo` cambió de False a True, notificar al usuario propietario del producto
    if not producto_viejo.listo and instance.listo:
        mensaje = f"Tu producto '{instance.descripcion}' ha sido marcado como 'Realizado'."
        Notificacion.objects.create(
            usuario=instance.user,  # Usuario que recibe la notificación
            mensaje=mensaje  # 🔹 Eliminamos usuario_origen
        )

    # Detectar cambios en otros campos importantes
    campos_importantes = ["categoria", "nota", "cantidad", "precio_compra", "importancia", "proveedor"]
    cambios = [campo for campo in campos_importantes if getattr(producto_viejo, campo, None) != getattr(instance, campo, None)]

    if cambios:
        mensaje = f"Tu producto '{instance.descripcion}' ha sido editado. Campos modificados: {', '.join(cambios)}."
        Notificacion.objects.create(
            usuario=instance.user,  # Usuario que recibe la notificación
            mensaje=mensaje  # 🔹 Eliminamos usuario_origen
        )


from django.http import HttpResponseForbidden
@login_required
def actualizar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    # Solo el usuario dueño del producto o un superusuario pueden editar
    if request.user != producto.user and not request.user.is_superuser:
        messages.error(request, "No tienes permisos para editar este producto.")
        return redirect('lista_productos')

    if request.method == 'POST':
        # Si NO es superusuario, solo puede modificar ciertos campos
        if not request.user.is_superuser:
            producto.sku = request.POST.get('sku', producto.sku)
            producto.descripcion = request.POST.get('descripcion', producto.descripcion)
            producto.importancia = request.POST.get('importancia', producto.importancia)
            producto.cantidad = request.POST.get('cantidad', producto.cantidad)
            producto.categoria = request.POST.get('categoria', producto.categoria)
        else:
            # Si es superusuario, puede modificar todo
            producto.sku = request.POST.get('sku', producto.sku)
            producto.descripcion = request.POST.get('descripcion', producto.descripcion)
            producto.importancia = request.POST.get('importancia', producto.importancia)
            producto.precio_compra = request.POST.get('precio_compra', producto.precio_compra)
            producto.proveedor = request.POST.get('proveedor', producto.proveedor)
            producto.nota = request.POST.get('nota', producto.nota)
            producto.cantidad = request.POST.get('cantidad', producto.cantidad)
            producto.categoria = request.POST.get('categoria', producto.categoria)

        try:
            producto.save()
            messages.success(request, "Producto actualizado correctamente.")
        except Exception as e:
            messages.error(request, f"Error al actualizar el producto: {str(e)}")

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


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import UsuarioPersonalizado

@login_required
@user_passes_test(es_admin)
def cambiar_rol_usuario(request, user_id):
    usuario = get_object_or_404(UsuarioPersonalizado, id=user_id)

    # Evitar que un admin se cambie a sí mismo el rol
    if request.user == usuario:
        messages.error(request, "No puedes cambiar tu propio rol.")
        return redirect("lista_usuarios")

    # Alternar el rol solo si el usuario NO es el mismo que hace la acción
    if usuario.is_superuser:
        usuario.rol = "cliente"
        usuario.is_superuser = False
        usuario.is_staff = False
    else:
        usuario.rol = "admin"
        usuario.is_superuser = True
        usuario.is_staff = True

    usuario.save()
    messages.success(request, f"Rol de {usuario.username} cambiado a {usuario.rol}.")
    return redirect("lista_usuarios")




def lista_proveedores(request):
    
    query = request.GET.get("q", "")
    
    # Filtrar proveedores si hay una búsqueda
    proveedores = Proveedor.objects.filter(
        Q(nombre__icontains=query) | 
        Q(marca__nombre__icontains=query) | 
        Q(categoria__nombre__icontains=query)
    ).distinct()


    paginator = Paginator(proveedores, 10)  
    page_number = request.GET.get("page")
    proveedores_page = paginator.get_page(page_number)

    marcas = Marca.objects.all()
    categorias = Categoria.objects.all()
    departamentos = Region.objects.filter(country__name="Colombia")
    ciudades = City.objects.filter(country__name="Colombia")

    return render(request, 'lista_proveedores.html', {
        'proveedores': proveedores_page,  # Cambiamos a la página paginada
        'marcas': marcas,
        'categorias': categorias,
        'departamentos': departamentos,
        'ciudades': ciudades,
        'query': query,  # Para mantener la búsqueda en el template
    })



@login_required

def agregar_proveedor(request):
    if request.method == 'POST':
        marca_id = request.POST.get('marca')
        categoria_id = request.POST.get('categoria')
        nombre = request.POST.get('nombre')
        celular = request.POST.get('celular')
        nota = request.POST.get('nota', '')
        departamento_id = request.POST.get('departamento')
        ciudad_id = request.POST.get('ciudad')
        imagen = request.FILES.get('imagen', None)

        marca = get_object_or_404(Marca, id=marca_id)
        categoria = Categoria.objects.filter(id=categoria_id).first()
        departamento = Region.objects.filter(id=departamento_id).first()
        ciudad = City.objects.filter(id=ciudad_id).first()

        # Si no se subió imagen, usar la de la marca
        if not imagen and marca.imagen:
            imagen = marca.imagen

        Proveedor.objects.create(
            marca=marca,
            categoria=categoria,
            nombre=nombre,
            celular=celular,
            nota=nota,
            departamento=departamento,
            ciudad=ciudad,
            imagen=imagen
        )

        messages.success(request, 'Proveedor agregado correctamente.')
        return redirect('lista_proveedores')

    marcas = Marca.objects.all()
    categorias = Categoria.objects.all()
    departamentos = Region.objects.filter(country__name="Colombia")
    ciudades = City.objects.filter(country__name="Colombia")

    return render(request, 'lista_proveedores.html', {
        'marcas': marcas,
        'categorias': categorias,
        'departamentos': departamentos,
        'ciudades': ciudades
    })

@login_required

def editar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == "POST":
        form = ProveedorForm(request.POST, instance=proveedor)
        if form.is_valid():
            form.save()
            messages.success(request, "Proveedor actualizado correctamente.")
    return redirect('lista_proveedores')

@login_required

def eliminar_proveedor(request, proveedor_id):
    proveedor = get_object_or_404(Proveedor, id=proveedor_id)
    if request.method == "POST":
        proveedor.delete()
        messages.success(request, "Proveedor eliminado correctamente.")
    return redirect('lista_proveedores')



def obtener_ciudades(request):
    departamento_id = request.GET.get('departamento_id')

    print(f"Departamento recibido: {departamento_id}")  # 🚀 Verificar si recibe datos

    if departamento_id:
        try:
            departamento_id = int(departamento_id)  # Convertimos a entero para evitar errores
            ciudades = City.objects.filter(region_id=departamento_id).values('id', 'name')
            ciudades_lista = list(ciudades)

            print("Ciudades enviadas:", ciudades_lista)  # 🚀 Verificar si hay ciudades

            return JsonResponse(ciudades_lista, safe=False)
        except ValueError:
            return JsonResponse([], safe=False)  # Si el ID no es un número, retorna vacío

    return JsonResponse([], safe=False)




from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.contrib import messages
from .models import Categoria
from .forms import CategoriaForm

def lista_categorias(request):
    query = request.GET.get("q", "")

    categorias = Categoria.objects.filter(nombre__icontains=query)

    paginator = Paginator(categorias, 10)  # 10 categorías por página
    page_number = request.GET.get("page")
    categorias_page = paginator.get_page(page_number)

    return render(request, 'categorias.html', {
        'categorias': categorias_page,
        'query': query,
    })

@login_required

def agregar_categoria(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        if not nombre:
            messages.error(request, 'El nombre de la categoría es obligatorio.')
            return redirect('lista_categorias')
        
        if Categoria.objects.filter(nombre=nombre).exists():
            messages.error(request, 'Ya existe una categoría con este nombre.')
            return redirect('lista_categorias')
        
        Categoria.objects.create(nombre=nombre)
        messages.success(request, 'Categoría agregada correctamente')
        return redirect('lista_categorias')
    
    return redirect('lista_categorias')

@login_required

def editar_categoria(request, id):
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=id)
        nuevo_nombre = request.POST.get('nombre', '').strip()

        if not nuevo_nombre:
            return JsonResponse({'error': 'El nombre de la categoría es obligatorio.'}, status=400)
        
        if Categoria.objects.filter(nombre=nuevo_nombre).exclude(id=id).exists():
            return JsonResponse({'error': 'Ya existe una categoría con este nombre.'}, status=400)
        
        categoria.nombre = nuevo_nombre
        categoria.save()
        return JsonResponse({'mensaje': 'Categoría actualizada correctamente.'})
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)

@login_required

def eliminar_categoria(request, categoria_id):
    if request.method == 'POST':
        categoria = get_object_or_404(Categoria, id=categoria_id)
        categoria.delete()
        return JsonResponse({'mensaje': 'Categoría eliminada correctamente.'})

    return JsonResponse({'error': 'Método no permitido.'}, status=405)


from django.shortcuts import render
from .models import Marca

from django.core.paginator import Paginator
from django.shortcuts import render
from .models import Marca, Categoria, Region, City

@login_required
def lista_marcas(request):
    # Filtrar marcas según la búsqueda, si se proporciona
    query = request.GET.get('q')
    if query:
        marcas = Marca.objects.filter(
            nombre__icontains=query
            )
    else:
        marcas = Marca.objects.all()
    
    # Paginación
    paginator = Paginator(marcas, 10)  # Muestra 10 marcas por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'lista_marcas.html', {
        'page_obj': page_obj,
        'categorias': Categoria.objects.all(),
        'departamentos': Region.objects.all(),
        'ciudades': City.objects.all(),
    })


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Marca, Categoria, Region, City
from .forms import MarcaForm


@login_required

def agregar_marca(request):
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        categoria_id = request.POST.get('categoria')
        departamento_id = request.POST.get('departamento')
        ciudad_id = request.POST.get('ciudad')
        imagen = request.FILES.get('imagen')

        categoria = Categoria.objects.get(id=categoria_id) if categoria_id else None
        departamento = Region.objects.get(id=departamento_id) if departamento_id else None
        ciudad = City.objects.get(id=ciudad_id) if ciudad_id else None

        Marca.objects.create(
            nombre=nombre,
            categoria=categoria,
            departamento=departamento,
            ciudad=ciudad,
            imagen=imagen
        )

        messages.success(request, 'Marca agregada correctamente.')
        return redirect('lista_marcas')

    return render(request, 'lista_marcas.html')

@login_required

def editar_marca(request, id):
    marca = get_object_or_404(Marca, id=id)

    if request.method == 'POST':
        form = MarcaForm(request.POST, request.FILES, instance=marca)
        if form.is_valid():
            old_imagen = marca.imagen  # Guardamos la imagen actual antes de actualizar
            form.save()

            # Actualizar imagen de los proveedores si corresponde
            for proveedor in marca.proveedores.all():
                if proveedor.imagen == old_imagen:  # Si el proveedor usaba la imagen antigua
                    proveedor.imagen = marca.imagen
                    proveedor.save()

            messages.success(request, 'Marca actualizada correctamente.')
            return redirect('lista_marcas')
        messages.error(request, 'Error al actualizar la marca.')

    categorias = Categoria.objects.all()
    departamentos = Region.objects.all()
    ciudades = City.objects.all()

    return render(request, 'lista_marcas.html', {
        'form': form,
        'marca': marca,
        'categorias': categorias,
        'departamentos': departamentos,
        'ciudades': ciudades
    })

@login_required
def eliminar_marca(request, id):
    if request.method == 'POST':
        marca = get_object_or_404(Marca, id=id)
        marca.delete()
        return JsonResponse({'mensaje': 'Marca eliminada correctamente.'})

    return JsonResponse({'error': 'Método no permitido.'}, status=405)


