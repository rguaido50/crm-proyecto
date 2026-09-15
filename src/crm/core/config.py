from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://crm:crm@localhost:5432/crm"
    database_url_test: str = "postgresql+psycopg://crm:crm@localhost:55432/crm_test"


settings = Settings()
