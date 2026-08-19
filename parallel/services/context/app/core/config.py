from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    DATABASE_URL: str

    WORKSPACE_SERVICE_URL: str
    HABITS_SERVICE_URL: str
    PROJECTS_SERVICE_URL: str
    GOALS_SERVICE_URL: str
    REMINDERS_SERVICE_URL: str
    GEMINI_API_KEY: str
    CONTEXT_MODEL: str

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
