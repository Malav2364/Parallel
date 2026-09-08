from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import settings

# from app.middleware.authentication import AuthenticationMiddleware
from app.core.lifespan import lifespan
from app.middleware.request_id import RequestIDMiddleware

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.get("/", tags=["Gateway"])
def root():
    return {"message": "Gateway is running"}


app.include_router(router)
