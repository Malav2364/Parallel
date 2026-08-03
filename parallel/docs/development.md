# Development Guide

## Overview

This document describes the recommended development workflow, project conventions, coding standards, and contribution process for the Parallel platform.

The goal is to keep every service consistent, maintainable, and production-ready.

---

# Development Environment

## Requirements

- Python 3.13+
- Git
- Docker
- UV Package Manager
- PostgreSQL
- SQLite (Testing)

---

# Initial Setup

Clone the repository

```bash
git clone https://github.com/<your-username>/Parallel.git
```

Navigate to the Identity Service

```bash
cd parallel/services/identity
```

Install dependencies

```bash
uv sync
```

Create an environment file

```bash
cp .env.example .env
```

Update the environment variables before running the application.

---

# Running the Application

Development server

```bash
uv run fastapi dev app/main.py
```

Production server

```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# Database Migrations

Generate a migration

```bash
uv run alembic revision --autogenerate -m "describe your changes"
```

Review the generated migration before applying it.

Apply the latest migration

```bash
uv run alembic upgrade head
```

Rollback one migration

```bash
uv run alembic downgrade -1
```

---

# Project Structure

```
app/
│
├── api/
├── core/
├── exceptions/
├── middleware/
├── models/
├── repositories/
├── schemas/
├── services/
├── templates/
└── main.py
```

---

# Development Principles

The project follows these principles:

- Clean Architecture
- Repository Pattern
- Dependency Injection
- SOLID Principles
- Separation of Concerns

---

# Layer Responsibilities

## API

Responsible for:

- HTTP Requests
- HTTP Responses
- Dependency Injection

No business logic should exist here.

---

## Services

Responsible for:

- Business rules
- Validation
- Authentication
- Email handling
- Coordination between repositories

---

## Repositories

Responsible only for database operations.

Repositories should not contain business logic.

---

## Models

Represent database tables and relationships.

---

## Schemas

Validate requests and responses.

---

# Code Style

Formatting

```bash
uv run black .
```

Verify formatting

```bash
uv run black --check .
```

Linting

```bash
uv run ruff check .
```

Auto-fix lint issues

```bash
uv run ruff check . --fix
```

---

# Testing

Run all tests

```bash
uv run pytest
```

Coverage

```bash
uv run pytest --cov=app --cov-report=html
```

Tests should be written for every new feature and bug fix.

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

# Git Workflow

Create a feature branch

```bash
git checkout -b feature/feature-name
```

Commit changes

```bash
git add .
git commit -m "feat(identity): add feature description"
```

Push changes

```bash
git push origin feature/feature-name
```

Open a Pull Request against the appropriate branch.

---

# Commit Message Convention

Use Conventional Commits.

Examples

```
feat(auth): add refresh token rotation

fix(jwt): prevent duplicate refresh tokens

refactor(user): simplify service layer

test(auth): add logout integration tests

docs(identity): update API documentation

ci: improve GitHub Actions workflow
```

---

# Pull Request Checklist

Before creating a Pull Request:

- Code builds successfully.
- Ruff passes.
- Black formatting passes.
- All tests pass.
- Coverage is maintained or improved.
- Documentation is updated when necessary.
- No sensitive information is committed.
- Docker image builds successfully.

---

# CI/CD Pipeline

Every Pull Request automatically runs:

- Dependency installation
- Ruff
- Black
- Integration tests
- Coverage
- Docker build

Pull requests should only be merged after all checks pass.

---

# Branch Strategy

Recommended branches:

```
main
│
develop
│
feature/*
│
bugfix/*
│
hotfix/*
```

---

# Future Development

Planned enhancements include:

- Role-Based Access Control (RBAC)
- Notification Service
- API Gateway
- User Profile Service
- Audit Logging
- Monitoring
- Kubernetes Deployment

---

# Contributing

When contributing:

- Follow the existing project structure.
- Keep functions focused and small.
- Prefer reusable components over duplication.
- Write tests for new functionality.
- Keep documentation up to date.
- Ensure CI passes before requesting review.

Consistency is more valuable than cleverness. A predictable codebase is easier to maintain, review, and extend.