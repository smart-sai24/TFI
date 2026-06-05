from functools import lru_cache
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    project_name: str = 'TFI Internship Operations & Analytics'
    environment: str = 'local'
    database_url: str = 'sqlite:///./tfi_local.db'
    secret_key: str = 'change-me-before-production'
    access_token_expire_minutes: int = 60
    refresh_token_expire_minutes: int = 60 * 24 * 7
    login_rate_limit_attempts: int = 5
    login_rate_limit_window_seconds: int = 60
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
    resend_from_email: str = ''
    whatsapp_api_token: str = ''
    whatsapp_phone_number_id: str = ''
    ai_live_enabled: bool = False
    ai_provider: str = 'local'
    openai_api_key: str = ''
    openai_model: str = 'gpt-5.5'
    gemini_api_key: str = ''
    gemini_model: str = 'gemini-1.5-pro'
    ai_request_timeout_seconds: int = 20
    ai_storage_dir: str = 'storage'
    # Keep `frontend_origins` as a simple comma-separated string to avoid
    # dotenv/JSON parsing errors. We'll normalize to a list in the app startup.
    frontend_origins: str = 'http://localhost:3000'

    # Use pydantic-settings v2 configuration helper so environment variables
    # are read case-insensitively and from the `.env` file.
    model_config = SettingsConfigDict(env_file='.env', case_sensitive=False)

    @model_validator(mode='after')
    def validate_production_security(self):
        production_names = {'prod', 'production', 'staging'}
        if self.environment.strip().lower() in production_names:
            if self.secret_key == 'change-me-before-production' or len(self.secret_key) < 32:
                raise ValueError('SECRET_KEY must be at least 32 characters in production-like environments')
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
