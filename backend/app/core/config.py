from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    database_url: str
    secret_key: str = "change-this-local-development-secret"
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"
    auth_mode: str = "local"
    keycloak_issuer_uri: str = ""
    keycloak_jwks_url: str = ""
    keycloak_audience: str = ""
    keycloak_username_claim: str = "preferred_username"
    keycloak_email_claim: str = "email"
    keycloak_full_name_claim: str = "name"
    app_context_path: str = ""
    server_port: int = 8000
    cors_origins: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
