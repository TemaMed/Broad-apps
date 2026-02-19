from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "gen-svc"
    env: str = "dev"
    http_timeout_s: float = 4.5

    postgres_dsn: str
    redis_dsn: str

    fal_api_key_primary: str
    fal_api_key_secondary: str | None = None

    webhook_signing_secret: str = "change-me"
    payments_webhook_secret: str = "payments-secret"

    rate_limit_per_minute: int = 10
    rate_limit_ban_seconds: int = 60

    webhook_retry_attempts: int = 5
    webhook_retry_interval_s: int = 15

    log_dir: str = "/var/log/app"
    log_level: str = "INFO"

settings = Settings()
