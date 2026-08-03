# Testing Guide

## Overview

The Identity Service uses automated integration testing to ensure that all authentication flows work correctly and remain stable as new features are added.

The test suite validates both successful and failure scenarios while keeping each test isolated from the others.

---

# Testing Stack

| Tool | Purpose |
|------|---------|
| Pytest | Test Framework |
| FastAPI TestClient | API Testing |
| SQLite | Test Database |
| Pytest-Cov | Code Coverage |

---

# Test Structure

```
tests/
│
├── conftest.py
├── database.py
├── factories.py
├── utils.py
│
├── test_register.py
├── test_login.py
├── test_refresh_tokens.py
├── test_logout.py
├── test_verify_email.py
└── test_password_reset.py
```

---

# Test Database

The production application uses PostgreSQL.

During testing, a dedicated SQLite database is used.

```
sqlite:///./test.db
```

Using a separate database guarantees that tests never modify production data.

---

# Database Isolation

Every test starts with a clean database.

The testing fixtures automatically:

1. Create tables.
2. Remove existing data before each test.
3. Execute the test.
4. Clean up resources.

This ensures that each test is independent and repeatable.

---

# Dependency Override

FastAPI's dependency injection system is overridden during testing.

Instead of the production database:

```
Production Database
```

tests use:

```
SQLite Test Database
```

through:

```
app.dependency_overrides
```

This keeps tests fast and isolated.

---

# Test Utilities

Common operations are extracted into reusable helper functions.

Examples include:

- Register and verify a user
- Login and obtain JWT tokens
- Create test data

This avoids duplicated setup code across test files.

---

# Test Factories

Reusable test data is stored in dedicated factories.

Example:

```python
USER_DATA = {
    "email": "user@example.com",
    "password": "Password@123",
    "first_name": "John",
    "last_name": "Doe",
}
```

Factories make tests easier to maintain and update.

---

# Mocking External Services

Email sending is mocked during testing.

This prevents:

- Sending real emails
- Network dependencies
- Rate limiting
- Slow test execution

Tests focus only on application logic.

---

# Current Test Coverage

The current integration test suite covers:

## Registration

- Successful registration
- Duplicate email
- Invalid email
- Missing required fields

---

## Login

- Successful login
- Invalid password
- Unknown user
- Unverified user
- Refresh token storage

---

## Refresh Tokens

- Successful refresh
- Refresh token rotation
- Old refresh token rejection
- Invalid refresh token
- Missing refresh token

---

## Logout

- Successful logout
- Logout with invalid token
- Logout with revoked token
- Missing refresh token

---

## Email Verification

- Successful verification
- Invalid verification token
- Already verified user
- Non-existent user

---

## Password Reset

- Forgot password
- Unknown email
- Successful password reset
- Invalid reset token
- Old password rejection
- New password acceptance
- Refresh token revocation

---

# Running Tests

Run all tests

```bash
uv run pytest
```

Run a specific file

```bash
uv run pytest tests/test_login.py
```

Run a specific test

```bash
uv run pytest tests/test_login.py::test_login_success
```

Verbose output

```bash
uv run pytest -v
```

---

# Coverage

Generate terminal coverage

```bash
uv run pytest --cov=app --cov-report=term-missing
```

Generate HTML coverage

```bash
uv run pytest --cov=app --cov-report=html
```

Open

```
htmlcov/index.html
```

to inspect detailed line-by-line coverage.

---

# Continuous Integration

Every Pull Request automatically runs:

- Ruff
- Black
- Integration Tests
- Coverage
- Docker Build

This ensures new code does not break existing functionality.

---

# Best Practices

When adding new functionality:

- Write tests before merging.
- Test both success and failure cases.
- Keep tests independent.
- Mock external services.
- Use reusable fixtures.
- Maintain high code coverage.

---

# Future Improvements

Planned enhancements include:

- Performance testing
- Load testing
- Security testing
- API contract testing
- Mutation testing
- End-to-end testing