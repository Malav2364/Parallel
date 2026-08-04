# Identity Service

The Identity Service is the authentication and user management service of the Parallel platform.

It is responsible for user registration, authentication, email verification, password management, JWT token generation, refresh token rotation, and session security.

---

# Features

## Authentication

## Features

- JWT Authentication
- Refresh Token Rotation
- Email Verification
- Forgot Password
- Password Reset
- Secure Logout
- Role-Based Access Control (RBAC)
- Dynamic Permission-Based Authorization
- SQLAlchemy ORM
- Alembic Database Migrations
- PostgreSQL
- Integration Testing with Pytest
- Ruff Linting & Formatting
- GitHub Actions CI

## Email Verification

- Send Verification Email
- Verify Email
- Resend Verification Email


## Security

- BCrypt Password Hashing
- Refresh Token Hashing
- JWT Authentication
- Email Verification Enforcement
- Session Revocation
- Password Reset Token
- Unique JWT IDs (JTI)

---

# Tech Stack

| Category | Technology |
|----------|------------|
| Language | Python 3.13 |
| Framework | FastAPI |
| ORM | SQLAlchemy |
| Validation | Pydantic |
| Database | PostgreSQL |
| Testing | SQLite |
| Migrations | Alembic |
| Authentication | JWT |
| Password Hashing | BCrypt |
| Package Manager | UV |
| Testing | Pytest |
| Linting | Ruff |
| Formatting | Black |
| CI | GitHub Actions |
| Containerization | Docker |

---

# Folder Structure

## Project Structure

app/
├── api/
├── core/
├── exceptions/
├── middleware/
├── models/
├── repositories/
├── schemas/
├── services/
└── utils/

migrations/
scripts/
tests/

---

# Architecture

The service follows a layered architecture.

```
HTTP Request
      │
      ▼
API Router
      │
      ▼
Service Layer
      │
      ▼
Repository Layer
      │
      ▼
Database
```

Each layer has a single responsibility.

- API handles HTTP requests and responses.
- Service contains business logic.
- Repository communicates with the database.
- Models define database tables.
- Schemas validate requests and responses.

---

# Authentication Flow

```
Register
    │
    ▼
Verification Email
    │
    ▼
Verify Email
    │
    ▼
Login
    │
    ├───────────────┐
    ▼               ▼
Access Token   Refresh Token
                    │
                    ▼
          Refresh Access Token
                    │
                    ▼
                 Logout
```

---

# RBAC Flow

```
User
 │
 ▼
Role
 │
 ▼
RolePermission
 │
 ▼
Permission
 │
 ▼
require_permission()
 │
 ▼
Allow / Deny
```

# Permissions are enforced using the `require_permission()` dependency.

Example:

```python
@router.post("/roles")
def create_role(
    current_user: User = Depends(
        require_permission("manage_roles"),
    ),
):
```
## Seed Default Roles & Permissions

Run:

```bash
python -m scripts.seed_roles_permissions
```
---

# API Endpoints

## Authentication

| Method | Endpoint |
|--------|----------|
| POST | /api/v1/auth/register |
| POST | /api/v1/auth/login |
| POST | /api/v1/auth/refresh |
| POST | /api/v1/auth/logout |

---

## Email Verification

| Method | Endpoint |
|--------|----------|
| GET | /api/v1/auth/verify-email |
| POST | /api/v1/auth/resend-verification |

---

## Password

| Method | Endpoint |
|--------|----------|
| POST | /api/v1/auth/forgot-password |
| POST | /api/v1/auth/reset-password |

---

# Environment Variables

Create a `.env` file in the service root.

Example:

```env
DATABASE_URL=
JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

SMTP_HOST=
SMTP_PORT=
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM=

FRONTEND_URL=
```

---

# Local Development

Install dependencies

```bash
uv sync
```

Run the development server

```bash
uv run fastapi dev app/main.py
```

---

# Database

Run migrations

```bash
uv run alembic upgrade head
```

Create a migration

```bash
uv run alembic revision --autogenerate -m "message"
```

---

# Running Tests

Run all tests

```bash
uv run pytest
```

Run coverage

```bash
uv run pytest --cov=app --cov-report=html
```

Coverage report

```
htmlcov/index.html
```

---

# Code Quality

Run Ruff

```bash
uv run ruff check .
```

Auto-fix Ruff issues

```bash
uv run ruff check . --fix
```

Format code

```bash
uv run black .
```

Verify formatting

```bash
uv run black --check .
```

---

# Docker

Build image

```bash
docker build -t parallel-identity .
```

Run container

```bash
docker run -p 8000:8000 parallel-identity
```

---

# CI Pipeline

GitHub Actions automatically performs:

- Repository Checkout
- Python Setup
- Dependency Installation
- Ruff Linting
- Black Formatting Check
- Integration Tests
- Coverage Generation
- Docker Build Validation

---

# Testing Strategy

The service uses integration testing with a dedicated SQLite database.

Current coverage includes:

- Registration
- Login
- Refresh Tokens
- Logout
- Email Verification
- Password Reset

Email sending is mocked during tests to avoid external dependencies.

---

# Roadmap

## Completed

- Authentication
- Email Verification
- Password Reset
- Refresh Token Rotation
- Integration Testing
- CI/CD

## In Progress

- Role-Based Access Control (RBAC)

## Planned

- User Profiles
- Notification Service
- API Gateway
- Audit Logs
- Monitoring