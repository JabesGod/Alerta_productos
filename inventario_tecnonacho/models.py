from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings

class Producto(models.Model):
    sku = models.CharField(max_length=100)
    descripcion = models.TextField()
    fecha = models.DateField(auto_now_add=True)
    hora = models.TimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE
    )
    precio_compra = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    importancia = models.IntegerField(choices=[(i, i) for i in range(1, 6)], null=True, blank=True)
    listo = models.BooleanField(default=False)
    proveedor = models.TextField( null=True, blank=True)
    nota = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.sku} - {self.descripcion}"

    def clean(self):
        """Valida que el SKU sea único si `listo` es False."""
        if Producto.objects.filter(sku=self.sku).exclude(pk=self.pk).exists():
            producto_existente = Producto.objects.get(sku=self.sku)
            if not producto_existente.listo:
                raise ValidationError(f"El SKU '{self.sku}' ya existe y no está marcado como listo.")

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
