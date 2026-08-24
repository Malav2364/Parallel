from app.core.config import settings

ROUTES = {
    "identity": settings.IDENTITY_SERVICE_URL,
    "projects": settings.PROJECTS_SERVICE_URL,
    "workspace": settings.WORKSPACE_SERVICE_URL,
    "context": settings.CONTEXT_SERVICE_URL,
}
