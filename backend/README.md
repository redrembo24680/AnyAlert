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
uvicorn app.main:app --reload
```

Health check: `GET /api/v1/health`
