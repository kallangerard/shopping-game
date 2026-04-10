# syntax=docker/dockerfile:1@sha256:4a43a54dd1fedceb30ba47e76cfcf2b47304f4161c0caeac2db1c61804ea3c91
FROM ghcr.io/astral-sh/uv:0.11.6@sha256:b1e699368d24c57cda93c338a57a8c5a119009ba809305cc8e86986d4a006754 AS uv

FROM python:3.14-slim@sha256:6869258bd3dd1e6947f4e9a375319809cd02f29312ed70aabe98d8086905cfd4 AS builder

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

FROM python:3.14-slim@sha256:6869258bd3dd1e6947f4e9a375319809cd02f29312ed70aabe98d8086905cfd4 AS runtime

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
