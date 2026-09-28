# 🔒 SecurePass

🌐 [Versión en español](README.md)

A password manager with security auditing and user authentication, built with **Django 5**, **PostgreSQL 15**, **cryptography (Fernet)** and **Docker**.

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org)
[![Django Version](https://img.shields.io/badge/Django-5.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Docker Compose](https://img.shields.io/badge/Docker-Compose-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Encryption](https://img.shields.io/badge/Encryption-Fernet_(AES%2BHMAC)-4B0082?style=for-the-badge&logo=letsencrypt&logoColor=white)](https://cryptography.io/en/latest/fernet/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white)](https://getbootstrap.com)
[![Deploy on Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge&logo=render&logoColor=white)](https://render.com)
[![Database on Neon](https://img.shields.io/badge/Database-Neon-00E599?style=for-the-badge&logo=postgresql&logoColor=white)](https://neon.com)

## Table of contents

- [Features](#features)
- [Conceptual UI overview](#conceptual-ui-overview)
- [Navigation flow](#navigation-flow)
- [Architecture](#architecture)
- [Data model](#data-model)
- [Project structure](#project-structure)
- [Quick start guide](#quick-start-guide)
- [Free deployment on Render + Neon](#free-deployment-on-render--neon)
- [Application routes](#application-routes)
- [Security notes](#security-notes)
- [Roadmap](#roadmap)

## Features

**Authentication and access control**
- Signup, login and logout with `django.contrib.auth`, plus system password validators (minimum length, not fully numeric, not a common password).
- Private dashboard protected with `LoginRequiredMixin` / `@login_required`; each user only sees, reveals and deletes their own credentials (queries are always filtered by `user`, no IDOR).

**Credential management**
- Add passwords with `site_name` (platform), `username_or_email` and a password, linked to the authenticated user.
- Symmetric encryption with **Fernet** (`cryptography`) before saving: the database never contains plaintext, only the encrypted token.
- On-demand reveal via an AJAX endpoint (`POST`, authenticated, verifies resource ownership) instead of shipping the password in the initial HTML.
- Deletion with a confirmation page.

**Security auditing**
- A strength analyzer (`passwords/utils.py`) that scores 1 to 5 based on length and character variety (uppercase, lowercase, digits, symbols), always computed server-side.
- Dashboard with aggregate stats: total passwords, average strength and number of weak passwords.

**Password generator**
- Cryptographically secure generation using Python's `secrets` module (not `random`), with configurable length and character types from the UI; guarantees at least one character of each selected type.

**UI**
- Dashboard layout with a sidebar, instant search, strength indicators and copy-to-clipboard, built on Bootstrap 5 + Bootstrap Icons.

**Infrastructure**
- Containerized deployment with Docker Compose (`web` + `db`), environment variables for every secret, and an `entrypoint.sh` that waits for PostgreSQL before migrating and starting Gunicorn.

## Conceptual UI overview

No real screenshots are included in the repository (you'd need to run it yourself to take those), but roughly:

- **Login / signup**: split-screen layout, a branding panel on the left and the form on the right.
- **Dashboard**: dark sidebar, stat cards up top, a credentials table with search, strength badges, and reveal/copy/delete buttons.
- **Add password**: a generator panel (length slider + option chips) kept visually separate from the save form.

## Navigation flow

```mermaid
flowchart TD
    %% ============================
    %% PUBLIC PAGES
    %% ============================
    A[Home] --> B[Log in]
    A --> C[Sign up]
    C --> B

    %% ============================
    %% PRIVATE DASHBOARD
    %% ============================
    B --> H[Dashboard]
    H --> H0[Stats: total, average strength, weak count]

    %% SEARCH AND MANAGEMENT
    H --> S[Search by site or username]
    H --> V[Reveal password]
    V --> V1[Copy to clipboard]
    H --> D[Delete password]
    D --> D1[Confirm deletion]
    D1 --> H

    %% ADD PASSWORD
    H --> N[Add password]
    N --> N1[Password generator]
    N1 --> N2[Length + character types]
    N2 --> N3[Generate with secrets - CSPRNG]
    N3 --> N4[Fill form field]
    N --> N5[Save credential]
    N5 --> N6[Analyze strength server-side]
    N6 --> N7[Encrypt with Fernet]
    N7 --> H

    %% ============================
    %% ADMINISTRATION
    %% ============================
    H --> P{Is staff?}
    P -->|Yes| Q[Django admin panel]
    P -->|No| H

    Q --> Q1[Manage users]
    Q --> Q2[View credential metadata]
    Q2 --> Q2N[No access to plaintext passwords]
    Q --> Q3[Create superusers]

    %% SESSION
    H --> X[Log out]
    X --> B
```

## Architecture

```
┌────────────┐        HTTP :8000        ┌──────────────────────┐
│  Browser   │ ───────────────────────▶ │  web (Django+Gunicorn)│
└────────────┘                          │  - Auth               │
                                         │  - passwords app      │
                                         │  - Fernet encryption  │
                                         └──────────┬────────────┘
                                                     │ SQL (internal
                                                     │ network, no exposed port)
                                         ┌──────────▼────────────┐
                                         │  db (PostgreSQL 15)    │
                                         │  persistent volume     │
                                         └────────────────────────┘
```

Both services are orchestrated with `docker-compose.yml`. `web` doesn't start until `db`'s `healthcheck` (`pg_isready`) confirms the database is ready.

## Data model

`StoredPassword` (app `passwords`):

| Field                 | Type               | Notes                                           |
|-----------------------|--------------------|--------------------------------------------------|
| `id`                  | `UUIDField`        | Primary key, not auto-incrementing               |
| `user`                | `ForeignKey(User)` | `on_delete=CASCADE`, `related_name="stored_passwords"` |
| `site_name`           | `CharField(150)`   | Platform or service                               |
| `username_or_email`   | `CharField(255)`   | Username or email associated with that account   |
| `encrypted_password`  | `TextField`        | Fernet token, never plaintext                     |
| `strength_score`      | `IntegerField`     | 1–5, computed server-side                         |
| `created_at`          | `DateTimeField`    | `auto_now_add`                                    |
| `updated_at`          | `DateTimeField`    | `auto_now`                                        |

## Project structure

```
SecurePass/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── entrypoint.sh
├── git_setup.sh            # Suggested initial commits (optional)
├── .env.example
├── .dockerignore
├── .gitignore
├── manage.py
├── config/                  # Django project configuration
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── passwords/                # Password manager app
│   ├── models.py             # StoredPassword model
│   ├── forms.py               # SignupForm, StoredPasswordForm
│   ├── views.py                # Dashboard, create, delete, reveal, generator, signup
│   ├── urls.py
│   ├── admin.py
│   ├── utils.py                 # Fernet encryption, strength analyzer, generator
│   └── migrations/
├── templates/
│   ├── base.html               # Shell with sidebar / topbar
│   ├── registration/
│   │   ├── login.html          # Split-screen layout
│   │   └── signup.html
│   └── passwords/
│       ├── dashboard.html       # Stats + table + search
│       ├── add_password.html    # Generator + create form
│       └── confirm_delete.html
└── static/
    └── css/style.css            # Design system (CSS variables, sidebar, badges)
```

## Quick start guide

### 1. Prerequisites

- Docker and Docker Compose installed.

### 2. Configure environment variables

```bash
cd SecurePass
cp .env.example .env
```

Edit `.env` and generate two required keys:

```bash
# Django SECRET_KEY
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# FERNET_KEY to encrypt stored passwords
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste both values into `SECRET_KEY` and `FERNET_KEY` in `.env`, and replace `POSTGRES_PASSWORD` with a strong password.

### 3. Start the environment with Docker Compose

```bash
docker-compose build
docker-compose up -d
```

This starts the `db` service (PostgreSQL 15) and the `web` service (Django + Gunicorn), waiting for the database to be healthy before starting Django.

### 4. Apply migrations

Migrations for `django.contrib.auth` and the other framework apps are applied automatically when the `web` container starts (see `entrypoint.sh`). To generate and apply migrations for the `passwords` app (first run, or after changing models):

```bash
docker-compose exec web python manage.py makemigrations passwords
docker-compose exec web python manage.py migrate
```

### 5. Create a superuser (optional, to access /admin/)

```bash
docker-compose exec web python manage.py createsuperuser
```

### 6. Access the application

- Application: http://localhost:8000/
- Signup: http://localhost:8000/signup/
- Login: http://localhost:8000/login/
- Admin panel: http://localhost:8000/admin/

### 7. View logs / stop the environment

```bash
docker-compose logs -f web
docker-compose down          # stops the containers
docker-compose down -v       # stops them and also removes the data volume
```

## Free deployment on Render + Neon

To keep the project live at a public URL at no cost, the `web` container is deployed on **Render** (free plan) and the database on **Neon** (free serverless Postgres, no expiration). These are two independent services, not `docker-compose`: each is deployed separately and connected via environment variables.

### 1. Create the database on Neon

1. Create an account at [neon.com](https://neon.com) and a new project (pick the region closest to where Render will run).
2. In the project dashboard, copy the **connection string**. It looks like this:
   ```
   postgresql://user:password@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
   ```
3. You can use the default database (`neondb`) or create one named `securepass_db` from Neon's SQL editor; if you do, update the name in the URL.

### 2. Push the code to GitHub

If you haven't already, follow the commits in `git_setup.sh` and `git push` to a repository (it can be private, Render can still access it).

### 3. Create the Web Service on Render

1. On [render.com](https://render.com), **New → Web Service** and connect your GitHub repository.
2. Under "Environment" choose **Docker** (Render auto-detects the `Dockerfile` at the repo root, no build command needed).
3. Plan: **Free**.
4. Under "Environment Variables" add:

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | Generate one with the command above, or use Render's "Generate" button |
   | `FERNET_KEY` | Generate one with `Fernet.generate_key()` and paste it as-is |
   | `DEBUG` | `False` |
   | `DATABASE_URL` | The connection string you copied from Neon in step 1 |

   No need to set `ALLOWED_HOSTS` or `CSRF_TRUSTED_ORIGINS`: `settings.py` detects the `RENDER_EXTERNAL_HOSTNAME` variable (Render injects it automatically) and self-configures, including forcing HTTPS.

5. Save and deploy. Render builds the image from your `Dockerfile` and runs `entrypoint.sh`, which waits for Neon to respond, applies migrations, collects static files (served with WhiteNoise, no nginx needed) and starts Gunicorn on the port Render assigns.

### 4. Create a superuser in production

From your service's **Shell** tab in the Render dashboard:

```bash
python manage.py createsuperuser
```

### 5. Things to keep in mind

- Render's free plan puts the service to sleep after a period without traffic; the first visit after waking up takes 30–60 seconds to respond. For an interview, load the URL yourself a couple of minutes beforehand.
- Neon scales to zero after 5 minutes of inactivity, but wakes up on its own in ~1 second on the next connection — no manual action required, unlike some other free alternatives.
- Every `git push` to the connected branch triggers an automatic redeploy (Render auto-deploys by default).

## Application routes

| Method | Route                    | View                    | Description                                        |
|--------|---------------------------|-------------------------|-----------------------------------------------------|
| GET/POST | `/signup/`             | `SignupView`            | User registration                                    |
| GET/POST | `/login/`              | `auth_views.LoginView`  | Login                                                |
| POST     | `/logout/`             | `auth_views.LogoutView` | Logout                                               |
| GET      | `/`                    | `DashboardView`         | Private dashboard with the user's credentials        |
| GET/POST | `/add/`                | `AddPasswordView`       | Add a new credential                                 |
| POST     | `/generate/`           | `generate_password`     | Generates a secure password (does not save it)       |
| POST     | `/<uuid:pk>/reveal/`   | `reveal_password`       | Decrypts and returns a password as JSON               |
| GET/POST | `/<uuid:pk>/delete/`   | `DeletePasswordView`    | Confirmation and deletion of a credential             |
| —        | `/admin/`              | Django admin             | Read-only/metadata deletion, no access to plaintext passwords |

## Security notes

- Stored passwords are encrypted with Fernet (AES-128 in CBC mode + HMAC-SHA256) using `FERNET_KEY`. If you lose that key, stored passwords can no longer be decrypted: keep it in a secrets manager, not in the repository.
- The reveal endpoint (`/<uuid>/reveal/`) and the generation endpoint (`/generate/`) only respond to authenticated `POST` requests; the former also verifies the credential belongs to the requesting user, preventing IDOR.
- The password generator uses `secrets` (a CSPRNG), never `random`, and doesn't persist anything until the user explicitly saves the form.
- Django's admin panel excludes `encrypted_password` from the form and has manual credential creation disabled (`has_add_permission = False`), so passwords can only ever be created through the application's encrypted flow.
- In real production use, it's recommended to serve the app behind HTTPS and enable `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` in `config/settings.py`.

## Roadmap

Reasonable ideas to keep maturing the project, not implemented yet:

- Two-factor authentication (TOTP) for the system login.
- Rate limiting on `/login/` and `/generate/` (e.g. `django-ratelimit`) against brute force.
- Automated tests (unit tests for `utils.py`, integration tests for the views) and CI.
- `FERNET_KEY` rotation with `MultiFernet` to be able to re-encrypt credentials without downtime.
- Encrypted export/import of credentials, and categories or tags per credential.
