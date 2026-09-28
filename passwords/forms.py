from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from passwords.models import StoredPassword


class SignupForm(UserCreationForm):
    """Formulario de registro de usuarios del sistema (extiende el de Django)."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "tu@correo.com"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Nombre de usuario"}
        )
        self.fields["password1"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Contraseña"}
        )
        self.fields["password2"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Confirma tu contraseña"}
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user


class StoredPasswordForm(forms.ModelForm):
    """
    Formulario para añadir una nueva credencial al gestor.

    El campo `password` es un campo de solo formulario (no pertenece al
    modelo): el backend lo cifra con Fernet y calcula la puntuación de
    fortaleza antes de guardar la instancia (ver views.AddPasswordView).
    """

    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": "Contraseña a guardar",
                "autocomplete": "new-password",
            }
        ),
        min_length=1,
    )

    class Meta:
        model = StoredPassword
        fields = ["site_name", "username_or_email"]
        widgets = {
            "site_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": 'Ej. "GitHub"'}
            ),
            "username_or_email": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Usuario o correo asociado"}
            ),
        }
        labels = {
            "site_name": "Servicio / Sitio web",
            "username_or_email": "Usuario o correo",
        }
