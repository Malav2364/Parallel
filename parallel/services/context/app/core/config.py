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
    GITHUB_SERVICE_URL: str = "http://github:8000/api/v1/github"
    GEMINI_API_KEY: str
    CONTEXT_MODEL: str

    # Tier-2 semantic project resolver (in-process cosine over Gemini
    # embeddings). A match requires the top project to clear THRESHOLD and to
    # lead the runner-up by at least MARGIN; otherwise the cascade defers to
    # the LLM resolver rather than guessing.
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    EMBEDDING_MATCH_THRESHOLD: float = 0.78
    EMBEDDING_MATCH_MARGIN: float = 0.06

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()
