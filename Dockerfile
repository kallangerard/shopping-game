# syntax=docker/dockerfile:1@sha256:4a43a54dd1fedceb30ba47e76cfcf2b47304f4161c0caeac2db1c61804ea3c91
FROM ghcr.io/astral-sh/uv:0.11.7@sha256:240fb85ab0f263ef12f492d8476aa3a2e4e1e333f7d67fbdd923d00a506a516a AS uv

FROM python:3.14-slim@sha256:71b358f8bff55413f4a6b95af80acb07ab97b5636cd3b869f35c3680d31d1650 AS builder

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.14-slim@sha256:71b358f8bff55413f4a6b95af80acb07ab97b5636cd3b869f35c3680d31d1650 AS runtime

RUN useradd --create-home appuser

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY manage.py ./
COPY shopping_game/ shopping_game/
COPY store/ store/

RUN mkdir -p media staticfiles \
    && chown -R appuser:appuser /app

USER appuser

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=shopping_game.settings \
    DEBUG=False \
    ALLOWED_HOSTS=*

EXPOSE 8000

CMD ["sh", "-c", "python manage.py migrate --noinput && \
     python manage.py collectstatic --noinput && \
     gunicorn shopping_game.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers 2 \
       --timeout 60"]
