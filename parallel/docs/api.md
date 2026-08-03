# API Documentation

## Overview

The Identity Service provides RESTful APIs for authentication, account verification, password management, and session handling.

Base URL

```
/api/v1
```

---

# Authentication

Authentication uses JWT Bearer Tokens.

Protected endpoints require:

```
Authorization: Bearer <access_token>
```

---

# Response Format

Successful responses return the requested resource.

Example:

```json
{
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
}
```

---

# Error Format

All API errors follow a standardized format.

```json
{
    "error": {
        "code": "AUTH_001",
        "message": "Email already registered"
    },
    "timestamp": "2026-08-03T09:15:22Z",
    "path": "/api/v1/auth/register"
}
```

---

# Authentication Endpoints

---

## Register User

### Endpoint

```
POST /api/v1/auth/register
```

### Request

```json
{
    "email": "user@example.com",
    "password": "Password@123",
    "first_name": "John",
    "last_name": "Doe"
}
```

### Success

```
201 Created
```

### Possible Errors

| Status | Description |
|---------|-------------|
|400|Email already registered|
|422|Validation error|

---

## Login

### Endpoint

```
POST /api/v1/auth/login
```

### Request

Uses OAuth2 form data.

```
username=user@example.com
password=Password@123
```

### Success

```
200 OK
```

Response

```json
{
    "access_token": "...",
    "refresh_token": "...",
    "token_type": "bearer"
}
```

### Possible Errors

| Status | Description |
|---------|-------------|
|401|Invalid credentials|
|403|Email not verified|

---

## Refresh Token

### Endpoint

```
POST /api/v1/auth/refresh
```

### Request

```json
{
    "refresh_token":"..."
}
```

### Success

```
200 OK
```

Returns

- New Access Token
- New Refresh Token

The previous refresh token is immediately revoked.

### Possible Errors

| Status | Description |
|---------|-------------|
|401|Invalid refresh token|
|401|Expired refresh token|
|401|Revoked refresh token|

---

## Logout

### Endpoint

```
POST /api/v1/auth/logout
```

### Request

```json
{
    "refresh_token":"..."
}
```

### Success

```
204 No Content
```

### Behaviour

The supplied refresh token is revoked and cannot be reused.

---

# Email Verification

---

## Verify Email

### Endpoint

```
GET /api/v1/auth/verify-email
```

### Query Parameter

```
token=<verification_token>
```

### Success

```
200 OK
```

### Errors

| Status | Description |
|---------|-------------|
|400|Already verified|
|401|Invalid token|
|404|User not found|

---

## Resend Verification Email

### Endpoint

```
POST /api/v1/auth/resend-verification
```

### Request

```json
{
    "email":"user@example.com"
}
```

### Success

```
200 OK
```

---

# Password Management

---

## Forgot Password

### Endpoint

```
POST /api/v1/auth/forgot-password
```

### Request

```json
{
    "email":"user@example.com"
}
```

### Success

```
200 OK
```

For security reasons, the endpoint always returns success even if the email does not exist.

---

## Reset Password

### Endpoint

```
POST /api/v1/auth/reset-password
```

### Request

```json
{
    "token":"...",
    "new_password":"Password@123"
}
```

### Success

```
200 OK
```

### Behaviour

- Updates the user's password.
- Revokes all active refresh tokens.
- Forces all devices to log in again.

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
     ▼
Access Token
Refresh Token
     │
     ▼
Protected APIs
     │
     ▼
Refresh Token
     │
     ▼
Logout
```

---

# HTTP Status Codes

| Code | Meaning |
|------|---------|
|200|Request successful|
|201|Resource created|
|204|Request successful with no response body|
|400|Bad request|
|401|Unauthorized|
|403|Forbidden|
|404|Resource not found|
|409|Conflict|
|422|Validation failed|
|500|Internal server error|

---

# Security Features

The Identity Service includes:

- BCrypt password hashing
- JWT authentication
- Refresh token rotation
- Refresh token hashing
- Email verification
- Password reset tokens
- Session revocation
- Structured error responses
- Token uniqueness using JTI

---

# Future API Endpoints

Upcoming APIs include:

```
GET    /users/me

PUT    /users/me

POST   /roles

GET    /roles

POST   /permissions

GET    /permissions
```

These endpoints will be introduced as the platform evolves with Role-Based Access Control (RBAC) and additional user management capabilities.