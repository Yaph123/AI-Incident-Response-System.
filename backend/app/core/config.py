from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://incident:incident@localhost:5433/incident_response"
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    slack_webhook_url: str = ""
    slack_bot_token: str = ""
    slack_default_channel: str = "#incidents"

    github_token: str = ""
    github_default_owner: str = ""
    github_default_repo: str = ""

    log_level: str = "INFO"
    require_approval_for_slack: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000


settings = Settings()
