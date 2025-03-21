from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from django.contrib.auth import get_user_model
from .models import Producto, UsuarioPersonalizado
from .models import Proveedor
from cities_light.models import Region, City
from .models import Categoria
from .models import Marca


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



class ProveedorForm(forms.ModelForm):
    class Meta:
        model = Proveedor
        fields = ['marca', 'categoria', 'nombre', 'celular', 'nota', 'departamento', 'ciudad']


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre']



from django import forms
from .models import Marca


class MarcaForm(forms.ModelForm):
    class Meta:
        model = Marca
        fields = ['nombre', 'categoria', 'departamento', 'ciudad', 'imagen']  # Agrega 'departamento' y 'ciudad'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ingrese el nombre'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'departamento': forms.Select(attrs={'class': 'form-select'}),  # Asegúrate de que el widget sea el correcto
            'ciudad': forms.Select(attrs={'class': 'form-select'}),  # Asegúrate de que el widget sea el correcto
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
