from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "PIOS Reminder Service"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"

    DATABASE_URL: str
    NOTIFICATIONS_SERVICE_URL: str
    MAX_RETRY_ATTEMPTS: int

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()