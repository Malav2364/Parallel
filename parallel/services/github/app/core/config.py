from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "PIOS GitHub Connector"
    APP_VERSION: str = "0.1.0"
    DATABASE_URL: str
    CONNECTOR_VAULT_KEY: str = ""
    NOTIFICATIONS_SERVICE_URL: str = ""
    WATCHER_POLL_INTERVAL: int = 300

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
