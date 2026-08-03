# Parallel

> A scalable microservices-based backend platform built with FastAPI, following clean architecture principles, secure authentication, automated testing, and CI/CD.

---

## 📖 Overview

Parallel is a modern backend platform designed using a microservices architecture. Each service is developed independently with a strong focus on scalability, maintainability, security, and developer experience.

The project follows Clean Architecture and Repository Pattern principles, making it easier to extend, test, and deploy individual services.

The first completed service is the **Identity Service**, which provides secure authentication and user management capabilities.

---

## ✨ Features

### Identity Service

- User Registration
- Secure Login
- JWT Authentication
- Refresh Token Rotation
- Email Verification
- Forgot Password
- Password Reset
- Logout
- Password Hashing using BCrypt
- Token Hashing before Database Storage
- Structured Exception Handling
- Centralized Logging
- Repository Pattern
- Service Layer Architecture
- Dependency Injection
- Automated Testing with Pytest
- GitHub Actions CI
- Docker Support

---

## 🏗️ Project Architecture

```
Parallel
│
├── services/
│   ├── identity/
│   ├── notification/
│   ├── gateway/
│   └── ...
│
├── docs/
│
├── .github/
│
└── README.md
```

Each service is independently developed, tested, and deployed while sharing common architectural principles.

---

## 🛠️ Tech Stack

### Backend

- Python 3.13
- FastAPI
- SQLAlchemy
- Alembic
- Pydantic
- JWT Authentication
- Passlib (BCrypt)

### Database

- PostgreSQL
- SQLite (Testing)

### Testing

- Pytest
- FastAPI TestClient
- Coverage.py

### DevOps

- Docker
- GitHub Actions
- Ruff
- Black
- UV Package Manager

---

## 🚀 Getting Started

Clone the repository

```bash
git clone https://github.com/<your-username>/Parallel.git
```

Navigate into the project

```bash
cd Parallel
```

Go to the Identity Service

```bash
cd parallel/services/identity
```

Install dependencies

```bash
uv sync
```

Run the application

```bash
uv run fastapi dev app/main.py
```

---

## 🧪 Running Tests

```bash
uv run pytest
```

Run with coverage

```bash
uv run pytest --cov=app --cov-report=html
```

Coverage report will be generated inside:

```
htmlcov/index.html
```

---

## 🐳 Docker

Build the Docker image

```bash
docker build -t parallel-identity .
```

Run the container

```bash
docker run -p 8000:8000 parallel-identity
```

---

## 📂 Documentation

Additional documentation is available inside the `docs/` directory.

- Architecture
- API Documentation
- Development Guide
- Testing Guide

---

## 🛣️ Roadmap

### ✅ Completed

- Identity Service
- Authentication
- JWT
- Refresh Tokens
- Email Verification
- Password Reset
- CI/CD Pipeline
- Integration Tests

### 🚧 In Progress

- Role Based Access Control (RBAC)

### 📅 Planned

- Notification Service
- API Gateway
- Audit Logging
- User Profile Service
- Service Discovery
- Monitoring & Metrics
- Kubernetes Deployment

---

## 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

Please create a feature branch, write tests for new functionality, and ensure all CI checks pass before opening a pull request.

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

**Malav Patel**

Built as part of the Parallel Microservices Platform.
