from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

# Formulario personalizado
class CustomUserCreationForm(UserCreationForm):
    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "form-control"}),
        help_text="La contraseña debe tener al menos 4 caracteres.",
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "form-control"}),
        strip=False,
    )

    class Meta:
        model = User
        fields = ("username", "password1", "password2")  # Eliminamos el campo 'email'
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 4:
            raise forms.ValidationError("La contraseña debe tener al menos 4 caracteres.")
        return password1


from django import forms
from .models import Producto

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['sku', 'descripcion', 'precio_compra', 'importancia']
