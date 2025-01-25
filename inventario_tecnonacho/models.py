from django.db import models
from django.conf import settings

class Producto(models.Model):
    sku = models.CharField(max_length=100, unique=True)
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
    proveedor = models.CharField(max_length=255, null=True, blank=True)  # Nuevo campo
    nota = models.TextField(null=True, blank=True)  # Nuevo campo

    def __str__(self):
        return f"{self.sku} - {self.descripcion}"
