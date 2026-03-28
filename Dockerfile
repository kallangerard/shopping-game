# syntax=docker/dockerfile:1
# ---------------------------------------------------------------------------- #
# Build stage – install dependencies with uv into /app/.venv
# ---------------------------------------------------------------------------- #
FROM ghcr.io/astral-sh/uv:0.11.2 AS uv

FROM python:3.12-slim AS builder

# Copy the uv binary from the official uv image
COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies (leverages Docker layer cache when lock file is unchanged)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# ---------------------------------------------------------------------------- #
# Runtime stage – lean final image
# ---------------------------------------------------------------------------- #
FROM python:3.12-slim AS runtime

# Create a non-root user for security
RUN useradd --create-home appuser

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source
COPY manage.py ./
COPY shopping_game/ shopping_game/
COPY store/ store/

# Make media and static dirs writable by appuser
RUN mkdir -p media staticfiles \
    && chown -R appuser:appuser /app

USER appuser

# Activate the venv
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=shopping_game.settings \
    DEBUG=False \
    ALLOWED_HOSTS=*

EXPOSE 8000

# Collect static files and run gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && \
     python manage.py collectstatic --noinput && \
     gunicorn shopping_game.wsgi:application \
       --bind 0.0.0.0:8000 \
       --workers 2 \
       --timeout 60"]
