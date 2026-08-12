# PIOS Workspace Service

The Workspace service owns workspaces and their life-domain spaces.

## Current phase

This phase provides a bootable FastAPI service with versioned Workspace and
Space routes, SQLAlchemy persistence entities, and the first Alembic migration.
Repositories and business operations remain intentionally small until the
domain actions are implemented.

Run locally with:

```bash
copy .env.example .env
uv run uvicorn app.main:app --reload --port 8003
```

Set `DATABASE_URL` in `.env` before starting the service.

Create or update the database schema with:

```bash
uv run alembic upgrade head
```

Generate future migrations with:

```bash
uv run alembic revision --autogenerate -m "describe the change"
```

The service exposes:

- `GET /`
- `GET /api/v1/workspaces`
- `POST /api/v1/workspaces/initialize`
- `GET /api/v1/spaces`
- `POST /api/v1/spaces`
- `GET /api/v1/spaces/{space_id}`
- `/docs`

Space requests require the temporary `X-User-Id` header. Initialize the
workspace first, then create a custom space with a request such as:

```json
{
  "name": "My Startup",
  "description": "Work and planning for my startup",
  "type": "custom",
  "visibility": "private"
}
```
