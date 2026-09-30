# Videoflix – Backend

Django REST API for **Videoflix**, a video streaming platform. Users sign up
with their email address, activate their account via email and watch videos
in 480p, 720p or 1080p. Uploaded videos are converted to HLS in the
background with FFmpeg.

The frontend is provided separately and communicates with this API via REST.

> **Status:** work in progress. Features and API endpoints are added to this
> README as soon as they are implemented.

## Tech stack

| Purpose | Tool |
|---|---|
| Web framework / API | Django, Django REST Framework |
| Authentication | djangorestframework-simplejwt (JWT in HttpOnly cookies, token blacklist) |
| CORS | django-cors-headers |
| Database | PostgreSQL |
| Cache and job queue | Redis, django-redis, Django RQ |
| Video conversion | FFmpeg |
| Web server | Gunicorn, WhiteNoise for static files |
| Container | Docker, Docker Compose |

## Requirements

- **Docker Desktop** (includes Docker Compose) – it must be running before
  you start the project
- **Git**

Python does not have to be installed locally. Everything runs inside the
containers.

## Installation

```bash
git clone https://github.com/SiriusSagittarius/Videoflix.git
cd Videoflix
cp .env.template .env
```

Open `.env` and replace the placeholder values, at least `SECRET_KEY`, the
`DB_*` and the `EMAIL_*` values (see [Configuration](#configuration-env)). Then build and start
the containers:

```bash
docker compose up --build
```

If `docker compose` is not available, use `docker-compose up --build`.

On every start the backend container waits for PostgreSQL, collects the
static files, runs the migrations, creates the admin account from `.env`,
starts an RQ worker and finally Gunicorn.

The admin panel is available at <http://localhost:8000/admin/>. Log in with
`DJANGO_SUPERUSER_USERNAME` and `DJANGO_SUPERUSER_PASSWORD`.

## Configuration (`.env`)

| Variable | Meaning |
|---|---|
| `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_PASSWORD`, `DJANGO_SUPERUSER_EMAIL` | Admin account, created on the first start |
| `SECRET_KEY` | Secret key of the Django project, a long random string |
| `DEBUG` | `True` for development, `False` in production |
| `ALLOWED_HOSTS` | Comma separated host names the backend answers to |
| `CSRF_TRUSTED_ORIGINS` | Comma separated frontend origins, trusted for CSRF and allowed for CORS (e.g. `http://127.0.0.1:5500`) |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD` | PostgreSQL database, user and password |
| `DB_HOST`, `DB_PORT` | PostgreSQL host and port (`db`, `5432` in Docker) |
| `REDIS_LOCATION` | Redis URL for the cache |
| `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB` | Redis connection for the RQ job queue |
| `EMAIL_HOST`, `EMAIL_PORT` | SMTP server that sends the account emails |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Login of the SMTP account |
| `EMAIL_USE_TLS`, `EMAIL_USE_SSL` | Encryption of the SMTP connection, only one of them may be `True` |
| `DEFAULT_FROM_EMAIL` | Sender address of the emails |

## API endpoints

All endpoints start with `/api/`. On invalid input the API answers with a
general message on purpose, so it does not reveal whether an email address
is already registered.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| POST | `/api/register/` | Create an inactive user from `email`, `password` and `confirmed_password` | – |

## Useful commands

```bash
docker compose logs -f web                                # follow the backend logs
docker compose exec web python manage.py makemigrations  # create migrations
docker compose exec web python manage.py migrate         # apply migrations
docker compose down                                       # stop the containers
docker compose down -v                                    # stop and delete database, media and static volumes
```

After a change to `requirements.txt`, rebuild the image with
`docker compose up --build`.

## Good to know

- **Line endings:** `backend.entrypoint.sh` must be saved with `LF` line
  endings, otherwise the container stops with
  `exec ./backend.entrypoint.sh: no such file or directory`.
  `.gitattributes` takes care of this on checkout, also on Windows.
- **Media files** (uploaded videos, HLS files, thumbnails) are stored in the
  Docker volume `videoflix_media`, not in the project folder.
- **Database password:** PostgreSQL stores the password when its volume is
  created. To change `DB_PASSWORD` later, remove the volumes first with
  `docker compose down -v`. This deletes all data.

## Project structure

```
core/                   Django settings and root URLs
auth_app/               User accounts and JWT cookie authentication
  api/                  Serializers, views, URLs and the cookie authentication class
  tokens.py             Token generator for the account activation link
backend.Dockerfile      Image of the backend container (Python 3.12, FFmpeg)
backend.entrypoint.sh   Start script: migrations, admin account, RQ worker, Gunicorn
docker-compose.yml      Services: web (Django), db (PostgreSQL), redis
.env.template           Template for the environment variables
requirements.txt        Python dependencies
```

## Credits and license

**Developed as part of the Developer Akademie GmbH advanced training program.**

The Docker setup (`backend.Dockerfile`, `backend.entrypoint.sh`,
`docker-compose.yml`, `.env.template`, `.dockerignore`) and the
[frontend](https://github.com/SiriusSagittarius/Videoflix-Frontend) are
provided by the Developer Akademie GmbH. The "Developer Akademie Learning
License (Non-commercial)" in [LICENSE.md](LICENSE.md) applies to these
provided components.
