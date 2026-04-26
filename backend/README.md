# AnyAlert Backend (FastAPI)

Popular clean architecture starter:

- `app/api` - HTTP layer (routers, endpoints)
- `app/services` - business logic
- `app/repositories` - data-access logic
- `app/models` - SQLAlchemy models
- `app/schemas` - Pydantic DTOs
- `app/core` - config and core settings
- `app/db` - DB session and metadata

## Run

```bash
pip install -e .[dev]
alembic upgrade head
uvicorn app.main:app --reload
```

Health check: `GET /api/v1/health`

## Auth API

- `POST /api/v1/auth/register` - create user and generate 6-digit email verification code
- `POST /api/v1/auth/verify-email` - verify email with `{ email, code }`
- `POST /api/v1/auth/login` - login with verified email and password, returns JWT token

In `DEBUG=true` mode, register response includes `dev_verification_code` for local testing.

## Email Sending (SMTP)

Real email sending is controlled by environment variables:

- `EMAIL_ENABLED`
- `EMAIL_FROM`
- `EMAIL_FROM_NAME`
- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `SMTP_USE_STARTTLS`
- `SMTP_USE_SSL`
- `SMTP_TIMEOUT_SECONDS`

When `EMAIL_ENABLED=true`, `POST /api/v1/auth/register` sends the 6-digit verification code to the user's email via SMTP.

## Alembic

```bash
alembic upgrade head
```

Initial migration: `202604260001_create_users_table`.

## Docker (backend + postgres + redis)

From project root:

```bash
docker compose up --build
```

Backend runs in reload mode in Docker (`uvicorn --reload`) and mounts `./backend` into `/app`, so code changes in `backend/app` are applied automatically without rebuilding the image.

Services:

- Backend: http://localhost:8000
- Postgres: localhost:5432
- Redis: localhost:6379
