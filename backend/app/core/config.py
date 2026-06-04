from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = 'TFI Internship Operations & Analytics'
    database_url: str = 'sqlite:///./tfi_local.db'
    secret_key: str = 'change-me-before-production'
    access_token_expire_minutes: int = 480
    demo_mode: bool = False
    max_upload_bytes: int = 8 * 1024 * 1024
    attendance_session_minutes: int = 90
    allowed_hosts: str = 'localhost,127.0.0.1,0.0.0.0,backend'
    initial_admin_email: str = ''
    initial_admin_password: str = ''
    initial_admin_name: str = 'TFI Administrator'
    initial_admin_role: str = 'Admin'
    firebase_project_id: str = ''
    cloudinary_url: str = ''
    resend_api_key: str = ''
    whatsapp_api_token: str = ''
    # Keep `frontend_origins` as a simple comma-separated string to avoid
    # dotenv/JSON parsing errors. We'll normalize to a list in the app startup.
    frontend_origins: str = 'http://localhost:3000'

    # Use pydantic-settings v2 configuration helper so environment variables
    # are read case-insensitively and from the `.env` file.
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
