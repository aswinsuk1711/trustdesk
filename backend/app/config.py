from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./trustdesk.db"
    ai_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    demo_token: str = "trustdesk-demo-token"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
