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
    keycloak_token_url: str = ""
    keycloak_jwks_url: str = ""
    keycloak_client_id: str = ""
    keycloak_client_secret: str = ""
    keycloak_scope: str = "openid profile email"
    keycloak_audience: str = ""
    keycloak_username_claim: str = "preferred_username"
    keycloak_email_claim: str = "email"
    keycloak_full_name_claim: str = "name"
    keycloak_phone_claim: str = "phone_number"
    keycloak_auto_create_users: bool = True
    keycloak_default_role: str = "client"
    local_admin_login_enabled: bool = True
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
