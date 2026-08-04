from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Parallel Identity Service"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DATABASE_URL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int
    SMTP_HOST: str
    SMTP_PORT: int
    SMTP_USERNAME: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_FROM_NAME: str = "Parallel Identity"
    SMTP_USE_TLS: bool = True
    FRONTEND_URL: str
    ADMIN_EMAIL: str = "admin@example.com"

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
