from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./trustdesk.db"
    ai_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4.1-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    demo_token: str = "trustdesk-demo-token"
    jwt_secret: str = "992d6c45e55d25fc3309955c75cbb7adca79b11c4cfba8b2fb869749940b6f3a"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = ""
    mail_server: str = "smtp.gmail.com"
    mail_port: int = 587

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
