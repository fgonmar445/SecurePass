"""
Utilidades de seguridad para SecurePass:

1. Cifrado simétrico (Fernet) de las contraseñas almacenadas, usando la
   clave definida en settings.FERNET_KEY (variable de entorno FERNET_KEY).
2. Analizador de fortaleza de contraseñas, que calcula una puntuación de
   1 a 5 en función de longitud, mayúsculas, minúsculas, números y símbolos.
"""

import re
import secrets
import string

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

_SYMBOLS = string.punctuation


class EncryptionKeyMissing(ImproperlyConfigured):
    """Se lanza cuando FERNET_KEY no está configurada en el entorno."""


def get_fernet() -> Fernet:
    """
    Devuelve una instancia de Fernet inicializada con la clave de cifrado
    de la aplicación (settings.FERNET_KEY).
    """
    key = settings.FERNET_KEY
    if not key:
        raise EncryptionKeyMissing(
            "FERNET_KEY no está definida. Genera una con "
            "`python -c \"from cryptography.fernet import Fernet; "
            "print(Fernet.generate_key().decode())\"` y añádela a tu archivo .env."
        )
    if isinstance(key, str):
        key = key.encode()
    return Fernet(key)


def encrypt_password(raw_password: str) -> str:
    """Cifra una contraseña en texto plano y devuelve el token como string."""
    fernet = get_fernet()
    token = fernet.encrypt(raw_password.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_password(encrypted_password: str) -> str:
    """
    Descifra un token generado por encrypt_password() y devuelve la
    contraseña en texto plano. Lanza ValueError si el token no es válido
    (por ejemplo, si fue cifrado con una clave FERNET_KEY distinta).
    """
    fernet = get_fernet()
    try:
        plaintext = fernet.decrypt(encrypted_password.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError(
            "No se pudo descifrar la contraseña: el token no es válido o "
            "fue cifrado con una clave distinta."
        ) from exc
    return plaintext.decode("utf-8")


def analyze_password_strength(password: str) -> int:
    """
    Analiza la fortaleza de una contraseña y devuelve una puntuación
    entera entre 1 (muy débil) y 5 (muy fuerte).

    Criterios evaluados:
      - Longitud (>= 8 y >= 12 caracteres)
      - Presencia de letras minúsculas
      - Presencia de letras mayúsculas
      - Presencia de dígitos
      - Presencia de símbolos/caracteres especiales
    """
    if not password:
        return 1

    score = 0

    length = len(password)
    if length >= 8:
        score += 1
    if length >= 12:
        score += 1

    has_lower = re.search(r"[a-z]", password) is not None
    has_upper = re.search(r"[A-Z]", password) is not None
    has_digit = re.search(r"\d", password) is not None
    has_symbol = any(char in _SYMBOLS for char in password)

    variety_count = sum([has_lower, has_upper, has_digit, has_symbol])

    if variety_count >= 2:
        score += 1
    if variety_count >= 3:
        score += 1
    if variety_count >= 4:
        score += 1

    # La puntuación final se limita al rango [1, 5]
    return max(1, min(score, 5))


def generate_secure_password(
    length: int = 16,
    use_upper: bool = True,
    use_lower: bool = True,
    use_digits: bool = True,
    use_symbols: bool = True,
) -> str:
    """
    Genera una contraseña aleatoria criptográficamente segura usando el
    módulo `secrets` (CSPRNG), no `random`.

    - `length`: longitud deseada, se limita al rango [8, 128] por seguridad.
    - `use_upper`, `use_lower`, `use_digits`, `use_symbols`: activan o
      desactivan cada tipo de carácter incluido en el resultado.

    Si el resultado debe incluir varios tipos de carácter, se garantiza
    que aparece al menos uno de cada tipo seleccionado (no deja la
    inclusión de mayúsculas/símbolos/etc. al azar).
    """
    length = max(8, min(int(length), 128))

    pools = []
    if use_lower:
        pools.append(string.ascii_lowercase)
    if use_upper:
        pools.append(string.ascii_uppercase)
    if use_digits:
        pools.append(string.digits)
    if use_symbols:
        pools.append(_SYMBOLS)

    # Si el usuario no selecciona ningún tipo, se usa un conjunto seguro
    # por defecto en lugar de generar una contraseña vacía o predecible.
    if not pools:
        pools = [string.ascii_lowercase, string.ascii_uppercase, string.digits]

    combined_pool = "".join(pools)
    rng = secrets.SystemRandom()

    # Garantiza al menos un carácter de cada tipo seleccionado...
    password_chars = [secrets.choice(pool) for pool in pools]
    # ...y rellena el resto de la longitud con selección aleatoria segura.
    password_chars += [
        secrets.choice(combined_pool) for _ in range(length - len(password_chars))
    ]
    rng.shuffle(password_chars)

    return "".join(password_chars)


def strength_label(score: int) -> str:
    """Devuelve una etiqueta legible para una puntuación de fortaleza."""
    labels = {
        1: "Muy débil",
        2: "Débil",
        3: "Aceptable",
        4: "Fuerte",
        5: "Muy fuerte",
    }
    return labels.get(score, "Desconocida")
