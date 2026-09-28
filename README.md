# SecurePass

Gestor de contraseñas con auditoría de seguridad y autenticación de usuarios, construido con **Django 5**, **PostgreSQL 15** y **Docker**.

## Características

- Registro, login y logout de usuarios (`django.contrib.auth`).
- Panel de control privado (`@login_required`) con las contraseñas del usuario autenticado.
- Cifrado simétrico de las contraseñas guardadas con **Fernet** (`cryptography`), nunca se almacenan en texto plano.
- Análisis automático de fortaleza de contraseñas (longitud, mayúsculas, minúsculas, números, símbolos) con puntuación de 1 a 5.
- Revelado de contraseñas bajo demanda vía endpoint AJAX protegido (evita exponer texto plano en el HTML inicial y valida propiedad del recurso para evitar IDOR).
- Despliegue containerizado con Docker Compose (servicios `web` + `db`).

## Estructura del proyecto

```
SecurePass/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── entrypoint.sh
├── .env.example
├── .dockerignore
├── .gitignore
├── manage.py
├── config/                # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── passwords/              # App del gestor de contraseñas
│   ├── models.py           # Modelo StoredPassword
│   ├── forms.py            # SignupForm, StoredPasswordForm
│   ├── views.py            # Dashboard, alta, borrado, revelado, signup
│   ├── urls.py
│   ├── admin.py
│   ├── utils.py             # Cifrado Fernet + analizador de fortaleza
│   └── migrations/
├── templates/
│   ├── base.html
│   ├── registration/
│   │   ├── login.html
│   │   └── signup.html
│   └── passwords/
│       ├── dashboard.html
│       ├── add_password.html
│       └── confirm_delete.html
└── static/
    └── css/style.css
```

## Guía de arranque rápido

### 1. Requisitos previos

- Docker y Docker Compose instalados.

### 2. Configurar variables de entorno

```bash
cd SecurePass
cp .env.example .env
```

Edita `.env` y genera dos claves obligatorias:

```bash
# SECRET_KEY de Django
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# FERNET_KEY para cifrar las contraseñas guardadas
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Pega ambos valores en `SECRET_KEY` y `FERNET_KEY` dentro de `.env`, y ajusta `POSTGRES_PASSWORD` por una contraseña fuerte.

### 3. Levantar el entorno con Docker Compose

```bash
docker-compose build
docker-compose up -d
```

Esto levanta el servicio `db` (PostgreSQL 15) y el servicio `web` (Django + Gunicorn), esperando a que la base de datos esté saludable antes de arrancar Django.

### 4. Aplicar migraciones

Las migraciones de `django.contrib.auth` y demás apps del framework se aplican automáticamente al arrancar el contenedor `web` (ver `entrypoint.sh`). Para generar y aplicar las migraciones de la app `passwords` (primera vez o tras cambiar modelos):

```bash
docker-compose exec web python manage.py makemigrations passwords
docker-compose exec web python manage.py migrate
```

### 5. Crear un superusuario (opcional, para acceder a /admin/)

```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Acceder a la aplicación

- Aplicación: http://localhost:8000/
- Registro: http://localhost:8000/signup/
- Login: http://localhost:8000/login/
- Panel de administración: http://localhost:8000/admin/

### 7. Ver logs / detener el entorno

```bash
docker-compose logs -f web
docker-compose down          # detiene los contenedores
docker-compose down -v       # detiene y borra también el volumen de datos
```

## Notas de seguridad

- Las contraseñas guardadas se cifran con Fernet (AES-128 en modo CBC + HMAC-SHA256) usando `FERNET_KEY`. Si pierdes esa clave, las contraseñas guardadas dejan de poder descifrarse: consérvala en un gestor de secretos, no en el repositorio.
- El endpoint de revelado (`/<uuid>/reveal/`) solo responde a peticiones `POST` autenticadas y verifica que la credencial pertenece al usuario que la solicita.
- En producción real, se recomienda servir la aplicación detrás de HTTPS y activar `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` en `config/settings.py`.
