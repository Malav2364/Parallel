from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str
    APP_ENV: str
    HOST: str
    PORT: int
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    IDENTITY_SERVICE_URL: str
    LOG_LEVEL: str
    REDIS_URL: str
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()