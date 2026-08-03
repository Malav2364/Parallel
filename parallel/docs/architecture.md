# Parallel Architecture

## Overview

Parallel is designed as a modular microservices platform where each service owns a single business domain and can be developed, tested, and deployed independently.

The architecture emphasizes:

- Scalability
- Maintainability
- Security
- Testability
- Separation of Concerns

---

# High Level Architecture

```
                Client
                   │
                   ▼
            API Gateway (Planned)
                   │
    ┌──────────────┼──────────────┐
    ▼              ▼              ▼
Identity      Notification     User Service
 Service         Service
```

Each service manages its own:

- Database
- Business Logic
- API
- Tests
- Docker Image

---

# Identity Service Architecture

The Identity Service follows a layered architecture.

```
HTTP Request
      │
      ▼
FastAPI Router
      │
      ▼
Service Layer
      │
      ▼
Repository Layer
      │
      ▼
SQLAlchemy Models
      │
      ▼
Database
```

---

# Layer Responsibilities

## API Layer

Responsible for:

- Request validation
- Dependency Injection
- Calling service methods
- Returning HTTP responses

Business logic is intentionally kept out of this layer.

---

## Service Layer

Contains all business logic.

Examples:

- Register User
- Login
- Verify Email
- Reset Password
- Refresh Tokens

The service layer coordinates repositories, email sending, authentication, and validation.

---

## Repository Layer

Responsible only for database operations.

Examples:

- Create User
- Update User
- Get User by Email
- Save Refresh Token
- Revoke Tokens

Repositories never contain business rules.

---

## Models

SQLAlchemy models define the database schema and relationships.

Current models include:

- User
- RefreshToken

Future models:

- Role
- Permission

---

## Schemas

Pydantic schemas validate incoming requests and outgoing responses.

They also provide automatic OpenAPI documentation.

---

# Request Lifecycle

Example: User Login

```
Client
   │
POST /login
   │
   ▼
Router
   │
   ▼
UserService.authenticate_user()
   │
   ▼
UserRepository.get_by_email()
   │
   ▼
Database
   │
   ▼
UserService
   │
Create JWT
   │
Save Refresh Token
   │
   ▼
Response
```

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
             Refresh Endpoint
                    │
                    ▼
             New Access Token
```

---

# Design Principles

The project follows:

- Clean Architecture
- Repository Pattern
- Dependency Injection
- SOLID Principles
- Separation of Concerns

---

# Future Architecture

The platform will eventually include:

- API Gateway
- RBAC
- Notification Service
- User Profile Service
- Audit Logging
- Monitoring
- Distributed Tracing
- Service Discovery
- Container Orchestration