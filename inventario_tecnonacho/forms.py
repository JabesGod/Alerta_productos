from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import Producto, UsuarioPersonalizado

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
        model = get_user_model()  # Se usa el modelo personalizado en lugar de auth.User
        fields = ("username", "password1", "password2")  
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
        }

    def clean_password1(self):
        password1 = self.cleaned_data.get("password1")
        if len(password1) < 4:
            raise forms.ValidationError("La contraseña debe tener al menos 4 caracteres.")
        return password1

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['sku', 'descripcion', 'precio_compra', 'importancia']

class CambiarContraseñaForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )

class FotoPerfilForm(forms.ModelForm):
    class Meta:
        model = UsuarioPersonalizado
        fields = ['foto_perfil']
        widgets = {
            'foto_perfil': forms.FileInput(attrs={"class": "form-control"})
        }
