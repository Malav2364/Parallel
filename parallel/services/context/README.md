## PIOS Context Service

The Context Service stores the user's current, versioned context state.

Run migrations and start the service with:

```powershell
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\uvicorn.exe app.main:app --reload --port 8004
```

Endpoints:

- `GET /health`
- `GET /api/v1/context`
- `PATCH /api/v1/context`
- `GET /api/v1/context/changes`
- `POST /api/v1/context/extract`
- `POST /api/v1/context/analyze`
- `POST /api/v1/context/process`

Context requests require the temporary internal `X-User-Id` header. Example:

```json
{
  "updates": {
    "occupation": "software developer",
    "interests": ["AI", "startups"],
    "goals": ["build an AI product"]
  }
}
```

Each update merges into the current state and increments its version.

The extraction endpoint uses Gemini 3 Flash Preview to propose structured
updates. It does not write context automatically; persisted context remains
owned by the Context Service.

The analysis endpoint combines extraction with the proposal-only Decision
Engine. Decisions contain multiple typed signals and one proposed action.

The process endpoint runs extraction, decision-making, and action execution.
Only `create_project` is currently executable; goal, habit, context, and Space
actions remain proposals.
