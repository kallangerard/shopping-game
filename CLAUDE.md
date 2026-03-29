# CLAUDE.md

## Project Overview

Django web app implementing a toy point-of-sale shopping game for kids. A single `store` app handles the full POS flow: item grid, session-based cart, checkout, and change display.

## Tech Stack

- **Python 3.12**, managed via `uv`
- **Django 6+** with SQLite (`db.sqlite3`)
- **Nix flake** for reproducible dev environment (`.envrc` uses `use flake`)

## Development Setup

```bash
# Enter nix dev shell (auto-runs `uv sync --frozen`)
nix develop

# Or with direnv
direnv allow
```

## Common Commands

```bash
# Run dev server
uv run python manage.py runserver

# Run tests
uv run python manage.py test --verbosity=2

# Run migrations
uv run python manage.py migrate

# Load sample items fixture
uv run python manage.py loaddata sample_items

# Create superuser (for admin panel at /admin/)
uv run python manage.py createsuperuser
```

## Project Structure

```
shopping_game/   # Django project settings, urls, wsgi/asgi
store/           # Main app: models, views, templates, tests, fixtures
  migrations/
  templates/store/
  fixtures/sample_items.json
manage.py
pyproject.toml
flake.nix
```

## Key Models (`store/models.py`)

- **Item** — name, price, availability, emoji or image thumbnail
- **Transaction** — total, amount given, change, timestamp
- **TransactionItem** — line items linking Transaction to Item with quantity/unit_price

## Application Flow

1. `/` — POS view: item grid + current cart (cart stored in Django session)
2. `/checkout/` — enter payment amount, validates sufficient funds
3. `/change/<pk>/` — receipt showing change and items purchased

Cart is session-based (not persisted to DB). Transactions are written to SQLite on successful checkout.

## Workflow Files

- All GitHub Actions workflow files must use the `.yaml` extension (not `.yml`)
- Glob patterns in `paths-ignore` (e.g. `*.md`) must be quoted to avoid YAML alias parsing errors

## CI

GitHub Actions runs tests via Nix:

```bash
nix develop --command sh -c "uv sync --frozen --no-dev && uv run python manage.py test --verbosity=2"
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `*` | Comma-separated allowed hosts |
| `CSRF_TRUSTED_ORIGINS` | `` | Comma-separated trusted origins (e.g. `http://localhost:8080`). Required in Docker when using a non-standard port. |

## Adding Dependencies

```bash
uv add <package>
# commit both pyproject.toml and uv.lock
```
