# 🔒 SecurePass

Gestor de contraseñas con auditoría de seguridad y autenticación de usuarios, construido con **Django 5**, **PostgreSQL 15**, **cryptography (Fernet)** y **Docker**.

`Python 3.10` · `Django 5.0` · `PostgreSQL 15` · `Docker Compose` · `Fernet (AES + HMAC)`

## Índice

- [Características](#características)
- [Capturas conceptuales de la interfaz](#capturas-conceptuales-de-la-interfaz)
- [Arquitectura](#arquitectura)
- [Modelo de datos](#modelo-de-datos)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Guía de arranque rápido](#guía-de-arranque-rápido)
- [Despliegue gratuito en Render + Neon](#despliegue-gratuito-en-render--neon)
- [Rutas de la aplicación](#rutas-de-la-aplicación)
- [Notas de seguridad](#notas-de-seguridad)
- [Próximas mejoras](#próximas-mejoras)

## Características

**Autenticación y control de acceso**
- Registro, login y logout con `django.contrib.auth`, validadores de contraseña de sistema (longitud mínima, no numéricas, no comunes).
- Panel privado protegido con `LoginRequiredMixin` / `@login_required`; cada usuario solo ve, revela y borra sus propias credenciales (consultas siempre filtradas por `user`, sin IDOR).

**Gestión de credenciales**
- Alta de contraseñas con `site_name` (plataforma), `username_or_email` y contraseña, vinculadas al usuario autenticado.
- Cifrado simétrico con **Fernet** (`cryptography`) antes de guardar: la base de datos nunca contiene texto plano, solo el token cifrado.
- Revelado bajo demanda vía endpoint AJAX (`POST`, autenticado, verifica propiedad del recurso) en lugar de enviar la contraseña en el HTML inicial.
- Borrado con página de confirmación.

**Auditoría de seguridad**
- Analizador de fortaleza (`passwords/utils.py`) que puntúa de 1 a 5 según longitud y variedad de caracteres (mayúsculas, minúsculas, números, símbolos), calculado siempre en el servidor.
- Panel con estadísticas agregadas: total de contraseñas, fortaleza media y número de contraseñas débiles.

**Generador de contraseñas**
- Generación criptográficamente segura con el módulo `secrets` de Python (no `random`), con longitud y tipos de carácter configurables desde la interfaz; garantiza al menos un carácter de cada tipo seleccionado.

**Interfaz**
- Layout de panel con navegación lateral, búsqueda instantánea, indicadores de fortaleza y copia al portapapeles, construido sobre Bootstrap 5 + Bootstrap Icons.

**Infraestructura**
- Despliegue containerizado con Docker Compose (`web` + `db`), variables de entorno para todos los secretos, `entrypoint.sh` que espera a PostgreSQL antes de migrar y arrancar Gunicorn.

## Capturas conceptuales de la interfaz

No se incluyen capturas reales en el repositorio (para eso tendrías que ejecutarlo y hacerlas tú), pero a grandes rasgos:

- **Login / registro**: pantalla dividida, panel de marca a la izquierda y formulario a la derecha.
- **Panel**: barra lateral oscura, tarjetas de estadísticas arriba, tabla de credenciales con búsqueda, badges de fortaleza y botones de revelar/copiar/eliminar.
- **Añadir contraseña**: panel de generador (slider de longitud + chips de opciones) separado del formulario de guardado.

## Arquitectura

```
┌────────────┐        HTTP :8000        ┌──────────────────────┐
│  Navegador │ ───────────────────────▶ │  web (Django+Gunicorn)│
└────────────┘                          │  - Auth               │
                                         │  - passwords app      │
                                         │  - Cifrado Fernet      │
                                         └──────────┬────────────┘
                                                     │ SQL (red interna,
                                                     │ sin puerto expuesto)
                                         ┌──────────▼────────────┐
                                         │  db (PostgreSQL 15)    │
                                         │  volumen persistente   │
                                         └────────────────────────┘
```

Ambos servicios se orquestan con `docker-compose.yml`. `web` no arranca hasta que el `healthcheck` de `db` (`pg_isready`) confirma que la base de datos está lista.

## Modelo de datos

`StoredPassword` (app `passwords`):

| Campo                | Tipo               | Notas                                           |
|-----------------------|--------------------|--------------------------------------------------|
| `id`                  | `UUIDField`        | Clave primaria, no autoincremental                |
| `user`                | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="stored_passwords"` |
| `site_name`           | `CharField(150)`   | Plataforma o servicio                             |
| `username_or_email`   | `CharField(255)`   | Usuario o correo asociado a esa cuenta            |
| `encrypted_password`  | `TextField`        | Token Fernet, nunca texto plano                   |
| `strength_score`      | `IntegerField`     | 1–5, calculado en el servidor                     |
| `created_at`          | `DateTimeField`    | `auto_now_add`                                    |
| `updated_at`          | `DateTimeField`    | `auto_now`                                        |

## Estructura del proyecto

```
SecurePass/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── entrypoint.sh
├── git_setup.sh            # Commits iniciales sugeridos (opcional)
├── .env.example
├── .dockerignore
├── .gitignore
├── manage.py
├── config/                  # Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── passwords/                # App del gestor de contraseñas
│   ├── models.py             # Modelo StoredPassword
│   ├── forms.py               # SignupForm, StoredPasswordForm
│   ├── views.py                # Dashboard, alta, borrado, revelado, generador, signup
│   ├── urls.py
│   ├── admin.py
│   ├── utils.py                 # Cifrado Fernet, analizador de fortaleza, generador
│   └── migrations/
├── templates/
│   ├── base.html               # Shell con sidebar / topbar
│   ├── registration/
│   │   ├── login.html          # Layout split-screen
│   │   └── signup.html
│   └── passwords/
│       ├── dashboard.html       # Estadísticas + tabla + búsqueda
│       ├── add_password.html    # Generador + formulario de alta
│       └── confirm_delete.html
└── static/
    └── css/style.css            # Sistema de diseño (variables CSS, sidebar, badges)
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

## Despliegue gratuito en Render + Neon

Para tener el proyecto vivo en una URL pública sin coste, se despliega el contenedor `web` en **Render** (plan gratuito) y la base de datos en **Neon** (Postgres serverless gratuito, sin caducidad). Son dos servicios independientes, no `docker-compose`: cada uno se despliega por separado y se conectan por variables de entorno.

### 1. Crear la base de datos en Neon

1. Crea una cuenta en [neon.com](https://neon.com) y un proyecto nuevo (elige la región más cercana a donde vaya a estar Render).
2. En el panel del proyecto, copia la **cadena de conexión** (Connection string). Tiene esta forma:
   ```
   postgresql://usuario:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
   ```
3. Puedes usar la base de datos por defecto (`neondb`) o crear una llamada `securepass_db` desde el editor SQL de Neon; en ese caso cambia el nombre en la URL.

### 2. Subir el código a GitHub

Si aún no lo hiciste, sigue los commits de `git_setup.sh` y haz `git push` a un repositorio (puede ser privado, Render puede acceder igualmente).

### 3. Crear el Web Service en Render

1. En [render.com](https://render.com), **New → Web Service** y conecta tu repositorio de GitHub.
2. En "Environment" elige **Docker** (Render detecta el `Dockerfile` de la raíz automáticamente, no hace falta indicar un build command).
3. Plan: **Free**.
4. En "Environment Variables" añade:

   | Variable | Valor |
   |---|---|
   | `SECRET_KEY` | Genera una con el comando de la sección anterior, o usa el botón "Generate" de Render |
   | `FERNET_KEY` | Genera una con `Fernet.generate_key()` y pégala tal cual |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | La cadena de conexión que copiaste de Neon en el paso 1 |

   No hace falta definir `ALLOWED_HOSTS` ni `CSRF_TRUSTED_ORIGINS`: `settings.py` detecta la variable `RENDER_EXTERNAL_HOSTNAME` (Render la inyecta sola) y se autoconfigura, incluyendo forzar HTTPS.

5. Guarda y despliega. Render construye la imagen con tu `Dockerfile` y ejecuta `entrypoint.sh`, que espera a que Neon responda, aplica migraciones, recolecta estáticos (servidos con WhiteNoise, sin nginx) y arranca Gunicorn en el puerto que Render indique.

### 4. Crear un superusuario en producción

Desde la pestaña **Shell** de tu servicio en el panel de Render:

```bash
python manage.py createsuperuser
```

### 5. Cosas a tener en cuenta

- El plan gratuito de Render duerme el servicio tras un rato sin tráfico; la primera visita después de dormir tarda entre 30 y 60 segundos en responder. Para una entrevista, carga tú la URL un par de minutos antes.
- Neon escala a cero tras 5 minutos de inactividad, pero se reactiva solo en ~1 segundo al recibir una conexión — no requiere ninguna acción manual, a diferencia de otras alternativas gratuitas.
- Cada `git push` a la rama conectada vuelve a desplegar automáticamente (Render hace auto-deploy por defecto).

## Rutas de la aplicación

| Método | Ruta                     | Vista                  | Descripción                                      |
|--------|--------------------------|-------------------------|---------------------------------------------------|
| GET/POST | `/signup/`             | `SignupView`            | Registro de usuarios                              |
| GET/POST | `/login/`              | `auth_views.LoginView`  | Inicio de sesión                                  |
| POST     | `/logout/`             | `auth_views.LogoutView` | Cierre de sesión                                  |
| GET      | `/`                    | `DashboardView`         | Panel privado con las credenciales del usuario    |
| GET/POST | `/add/`                | `AddPasswordView`       | Alta de una nueva credencial                      |
| POST     | `/generate/`           | `generate_password`     | Genera una contraseña segura (no la guarda)       |
| POST     | `/<uuid:pk>/reveal/`   | `reveal_password`       | Descifra y devuelve una contraseña en JSON        |
| GET/POST | `/<uuid:pk>/delete/`   | `DeletePasswordView`    | Confirmación y borrado de una credencial          |
| —        | `/admin/`              | Django admin             | Solo lectura/borrado de metadatos, sin acceso a contraseñas en texto plano |

## Notas de seguridad

- Las contraseñas guardadas se cifran con Fernet (AES-128 en modo CBC + HMAC-SHA256) usando `FERNET_KEY`. Si pierdes esa clave, las contraseñas guardadas dejan de poder descifrarse: consérvala en un gestor de secretos, no en el repositorio.
- El endpoint de revelado (`/<uuid>/reveal/`) y el de generación (`/generate/`) solo responden a peticiones `POST` autenticadas; el primero además verifica que la credencial pertenece al usuario que la solicita, evitando IDOR.
- El generador de contraseñas usa `secrets` (CSPRNG), nunca `random`, y no persiste nada hasta que el usuario guarda el formulario explícitamente.
- El panel de administración de Django excluye `encrypted_password` del formulario y tiene deshabilitada la creación manual de credenciales (`has_add_permission = False`), para que las contraseñas solo puedan crearse a través del flujo cifrado de la aplicación.
- En producción real, se recomienda servir la aplicación detrás de HTTPS y activar `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` y `CSRF_COOKIE_SECURE` en `config/settings.py`.

## Próximas mejoras

Ideas razonables para seguir madurando el proyecto, no implementadas todavía:

- Autenticación de dos factores (TOTP) para el login del sistema.
- Rate limiting en `/login/` y `/generate/` (p. ej. `django-ratelimit`) contra fuerza bruta.
- Tests automatizados (unitarios para `utils.py`, de integración para las vistas) y CI.
- Rotación de `FERNET_KEY` con `MultiFernet` para poder re-cifrar credenciales sin downtime.
- Exportación/importación cifrada de credenciales y categorías o etiquetas por credencial.
