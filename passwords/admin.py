from django.contrib import admin

from passwords.models import StoredPassword


@admin.register(StoredPassword)
class StoredPasswordAdmin(admin.ModelAdmin):
    # Nunca se muestra encrypted_password en el listado ni en el formulario
    # de administración: solo metadatos no sensibles.
    list_display = (
        "site_name",
        "username_or_email",
        "user",
        "strength_score",
        "created_at",
    )
    list_filter = ("strength_score", "created_at")
    search_fields = ("site_name", "username_or_email", "user__username")
    readonly_fields = ("id", "created_at", "updated_at")
    exclude = ("encrypted_password",)
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        # Las credenciales solo deben crearse a través del flujo de la
        # aplicación (que las cifra correctamente antes de guardarlas),
        # nunca manualmente desde el admin.
        return False
