from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DeleteView, ListView

from passwords.forms import SignupForm, StoredPasswordForm
from passwords.models import StoredPassword
from passwords.utils import (
    analyze_password_strength,
    encrypt_password,
    generate_secure_password,
    strength_label,
)


class SignupView(CreateView):
    """Vista de registro de nuevos usuarios."""

    form_class = SignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, "Cuenta creada correctamente. Ya puedes iniciar sesión."
        )
        return response


class DashboardView(LoginRequiredMixin, ListView):
    """
    Panel de control privado: lista únicamente las contraseñas guardadas
    por el usuario autenticado.
    """

    model = StoredPassword
    template_name = "passwords/dashboard.html"
    context_object_name = "stored_passwords"
    login_url = "login"

    def get_queryset(self):
        return StoredPassword.objects.filter(user=self.request.user)


class AddPasswordView(LoginRequiredMixin, CreateView):
    """
    Vista para añadir una nueva contraseña. El backend analiza
    automáticamente la fortaleza de la contraseña introducida (longitud,
    mayúsculas, minúsculas, números y símbolos), calcula una puntuación
    de 1 a 5, cifra el valor con Fernet y lo guarda vinculado al usuario
    autenticado.
    """

    model = StoredPassword
    form_class = StoredPasswordForm
    template_name = "passwords/add_password.html"
    success_url = reverse_lazy("dashboard")
    login_url = "login"

    def form_valid(self, form):
        raw_password = form.cleaned_data["password"]

        stored_password = form.save(commit=False)
        stored_password.user = self.request.user
        stored_password.strength_score = analyze_password_strength(raw_password)
        stored_password.encrypted_password = encrypt_password(raw_password)
        stored_password.save()

        messages.success(
            self.request,
            f'Contraseña para "{stored_password.site_name}" guardada correctamente '
            f"(fortaleza: {stored_password.strength_label}).",
        )
        return redirect(self.success_url)


class DeletePasswordView(LoginRequiredMixin, DeleteView):
    """Elimina una credencial guardada, verificando que pertenece al usuario autenticado."""

    model = StoredPassword
    template_name = "passwords/confirm_delete.html"
    success_url = reverse_lazy("dashboard")
    login_url = "login"
    context_object_name = "stored_password"

    def get_queryset(self):
        # Evita IDOR: un usuario solo puede borrar sus propias credenciales.
        return StoredPassword.objects.filter(user=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, "Contraseña eliminada correctamente.")
        return super().form_valid(form)


@login_required
@require_POST
def reveal_password(request, pk):
    """
    Endpoint AJAX que descifra y devuelve, en JSON, la contraseña en texto
    plano de una credencial concreta. Solo responde si la credencial
    pertenece al usuario autenticado (evita IDOR) y solo acepta POST para
    no dejar rastro en logs de acceso vía querystring.
    """
    stored_password = get_object_or_404(StoredPassword, pk=pk, user=request.user)
    try:
        plaintext = stored_password.get_decrypted_password()
    except ValueError:
        return JsonResponse(
            {"error": "No se pudo descifrar la contraseña."}, status=500
        )
    return JsonResponse({"password": plaintext})


def _parse_bool(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "on", "yes")


@login_required
@require_POST
def generate_password(request):
    """
    Endpoint AJAX que genera una contraseña aleatoria segura (módulo
    `secrets`, CSPRNG) según los parámetros elegidos por el usuario:
    longitud, mayúsculas, minúsculas, números y símbolos. La contraseña
    generada NO se guarda aquí: solo se devuelve para rellenar el
    formulario de alta; el guardado (cifrado + puntuación) ocurre en
    AddPasswordView cuando el usuario envía el formulario.
    """
    try:
        length = int(request.POST.get("length", 16))
    except (TypeError, ValueError):
        length = 16

    use_upper = _parse_bool(request.POST.get("use_upper", "true"))
    use_lower = _parse_bool(request.POST.get("use_lower", "true"))
    use_digits = _parse_bool(request.POST.get("use_digits", "true"))
    use_symbols = _parse_bool(request.POST.get("use_symbols", "true"))

    password = generate_secure_password(
        length=length,
        use_upper=use_upper,
        use_lower=use_lower,
        use_digits=use_digits,
        use_symbols=use_symbols,
    )
    score = analyze_password_strength(password)

    return JsonResponse(
        {
            "password": password,
            "strength_score": score,
            "strength_label": strength_label(score),
        }
    )
