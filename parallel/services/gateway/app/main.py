from fastapi import FastAPI

from app.api.router import router
from app.core.config import settings

# from app.middleware.authentication import AuthenticationMiddleware
from app.core.lifespan import lifespan
from app.middleware.request_id import RequestIDMiddleware

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)


@app.get("/", tags=["Gateway"])
def root():
    return {"message": "Gateway is running"}


app.include_router(router)
