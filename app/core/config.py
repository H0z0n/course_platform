from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    db_echo: bool = False
    secret_key: str
    access_token_expire_minutes: int = 60 * 24
    password_reset_expire_minutes: int = 60
    site_name: str = "Course Platform"
    public_url: str = "http://localhost:5173"
    currency: str = "RUB"
    demo_payments: bool = False
    cors_origins: list[str] = []
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str = "noreply@example.com"
    smtp_starttls: bool = True
    smtp_ssl: bool = False
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
