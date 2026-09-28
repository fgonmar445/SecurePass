import uuid

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from passwords.utils import decrypt_password, strength_label


class StoredPassword(models.Model):
    """
    Representa una credencial (usuario/contraseña) de un servicio externo,
    guardada de forma cifrada y vinculada al usuario del sistema que la
    registró.
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="stored_passwords",
        verbose_name="Usuario",
    )
    site_name = models.CharField(
        max_length=150,
        verbose_name="Servicio / Sitio web",
        help_text='Nombre del servicio o web, ej. "GitHub".',
    )
    username_or_email = models.CharField(
        max_length=255,
        verbose_name="Usuario o correo asociado",
    )
    encrypted_password = models.TextField(
        verbose_name="Contraseña cifrada",
        help_text="Contraseña cifrada con Fernet (AES-128 + HMAC). Nunca se guarda en texto plano.",
    )
    strength_score = models.IntegerField(
        verbose_name="Puntuación de fortaleza",
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=1,
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Contraseña almacenada"
        verbose_name_plural = "Contraseñas almacenadas"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "site_name"]),
        ]

    def __str__(self):
        return f"{self.site_name} ({self.username_or_email}) — {self.user.username}"

    def get_decrypted_password(self) -> str:
        """Descifra y devuelve la contraseña en texto plano (uso puntual, bajo demanda)."""
        return decrypt_password(self.encrypted_password)

    @property
    def strength_label(self) -> str:
        return strength_label(self.strength_score)
