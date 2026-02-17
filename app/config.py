"""Application configuration using Pydantic Settings."""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = Field(default="Multi-Tenant SaaS API")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    secret_key: str = Field(...)
    
    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    workers: int = Field(default=4)
    
    # Supabase
    supabase_url: str = Field(...)
    supabase_anon_key: str = Field(...)
    supabase_service_role_key: str = Field(...)
    supabase_jwt_secret: str = Field(...)
    
    # Database
    database_url: str = Field(...)
    db_pool_size: int = Field(default=20)
    db_max_overflow: int = Field(default=10)
    
    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")
    redis_max_connections: int = Field(default=50)
    
    # Celery
    celery_broker_url: str = Field(default="redis://localhost:6379/1")
    celery_result_backend: str = Field(default="redis://localhost:6379/2")
    
    # Brevo
    brevo_api_key: str = Field(default="")
    brevo_sms_sender: str = Field(default="YourBrand")
    brevo_email_sender: str = Field(default="noreply@yourdomain.com")
    
    # VAPI
    vapi_api_key: str = Field(default="")
    vapi_phone_number: str = Field(default="")
    
    # Security
    encryption_key: str = Field(...)
    cors_origins: str = Field(default="http://localhost:3000")
    
    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60)
    rate_limit_per_hour: int = Field(default=1000)
    
    # Feature Flags
    enable_audit_logs: bool = Field(default=True)
    enable_rate_limiting: bool = Field(default=True)
    enable_circuit_breaker: bool = Field(default=True)
    
    # Monitoring
    sentry_dsn: str = Field(default="")
    log_level: str = Field(default="INFO")
    
    @field_validator("cors_origins")
    @classmethod
    def parse_cors_origins(cls, v: str) -> List[str]:
        """Parse comma-separated CORS origins."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.app_env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
