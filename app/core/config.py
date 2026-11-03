from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    database_url: str
    db_echo: bool = False
    secret_key: str
    access_token_expire_minutes: int = 60 * 24
    site_name: str = "Course Platform"
    currency: str = "RUB"
    demo_payments: bool = False
    cors_origins: list[str] = []
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
