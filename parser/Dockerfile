FROM mcr.microsoft.com/playwright/python:v1.58.0-jammy

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml .

RUN pip install --upgrade pip setuptools && \
    pip install -e .

COPY . .

# Run Celery worker by default
CMD ["celery", "-A", "app.worker.celery_app", "worker", "--loglevel=info", "-B"]
