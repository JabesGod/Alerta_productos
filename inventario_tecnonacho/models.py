from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db import models
from cities_light.models import Region, City 
class Producto(models.Model):
    CATEGORIAS = [
        ('faltantes', 'Faltantes'),
        ('demasiadas_existencias', 'Demasiadas existencias'),
        ('bajo_pedido', 'Bajo pedido'),
        ('realizados', 'Realizados'),
        ('agotados', 'Agotados con el proveedor')
    ]

    sku = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField()
    cantidad = models.IntegerField(default=0)  # Ahora es un número entero
    categoria = models.CharField(
        max_length=25, 
        choices=CATEGORIAS, 
        default='faltantes'
    )
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    precio_compra = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    importancia = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    listo = models.BooleanField(default=False)
    proveedor = models.TextField(null=True, blank=True)
    nota = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku} - {self.descripcion} - {self.categoria}"

    def clean(self):
        """Valida que el SKU sea único si `listo` es False y valida la categoría."""
        if Producto.objects.filter(sku=self.sku).exclude(pk=self.pk).exists():
            producto_existente = Producto.objects.get(sku=self.sku)
            if not producto_existente.listo:
                raise ValidationError(f"El SKU '{self.sku}' ya existe y no está marcado como listo.")

        if self.categoria not in dict(self.CATEGORIAS).keys():
            raise ValidationError("Categoría no válida. Usa una de las opciones predefinidas.")


from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models

class UsuarioPersonalizado(AbstractUser):
    foto_perfil = models.ImageField(upload_to='perfil/', null=True, blank=True)

    groups = models.ManyToManyField(
        Group,
        related_name="usuario_personalizado_groups",
        blank=True
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name="usuario_personalizado_permissions",
        blank=True
    )

    def __str__(self):
        return self.username
    


class Notificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.username} - {self.mensaje}"


class Categoria(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.nombre


class Marca(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to='marcas/', null=True, blank=True)
    departamento = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    ciudad = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)

    def save(self, *args, **kwargs):
        """Actualiza la imagen de los proveedores si cambia la imagen de la marca."""
        if self.pk:  # Si la marca ya existe
            old_marca = Marca.objects.get(pk=self.pk)
            if old_marca.imagen != self.imagen:  # Si la imagen cambió
                for proveedor in self.proveedores.all():  # `related_name="proveedores"`
                    if proveedor.imagen == old_marca.imagen:  # Solo si usaba la imagen de la marca
                        proveedor.imagen = self.imagen
                        proveedor.save()  # Guardar proveedor con la nueva imagen

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre



class Proveedor(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name="proveedores")
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)
    nombre = models.CharField(max_length=255)
    celular = models.CharField(max_length=15, help_text="Número de contacto")
    nota = models.TextField(null=True, blank=True)
    departamento = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    ciudad = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    imagen = models.ImageField(upload_to='proveedores/', null=True, blank=True)

    def save(self, *args, **kwargs):
        """Si el proveedor no tiene imagen, usa la imagen de la marca."""
        if not self.imagen and self.marca and self.marca.imagen:
            self.imagen = self.marca.imagen
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nombre} - {self.marca.nombre}"