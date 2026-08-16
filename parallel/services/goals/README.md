# Goals Service

The Goals Service owns durable, user-scoped goals.

Endpoints:

- `POST /api/v1/goals`
- `GET /api/v1/goals`

Requests use the `X-User-Id` header. Creating the same goal name for the same
user is idempotent and returns the existing goal.
