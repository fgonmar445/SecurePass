"""Rutas principales del proyecto SecurePass."""

from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from passwords.views import SignupView

urlpatterns = [
    path("admin/", admin.site.urls),

    # --- Autenticación ---
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("signup/", SignupView.as_view(), name="signup"),

    # --- Gestor de contraseñas (dashboard, alta, borrado, revelar) ---
    path("", include("passwords.urls")),
]
