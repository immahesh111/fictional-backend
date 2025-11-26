from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "sqlite:///./face_detection.db"
    
    # JWT Authentication
    secret_key: str = "your-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours
    
    # MQTT Configuration
    mqtt_broker: str = "ed725a79580548b5a05651ec325d471d.s1.eu.hivemq.cloud"
    mqtt_port: int = 8883
    mqtt_username: Optional[str] = "Mahesh"
    mqtt_password: Optional[str] = "Voxov123"
    mqtt_topic_prefix: str = "factory/machine"
    mqtt_use_tls: bool = True
    
    # File upload settings
    upload_dir: str = "./uploads"
    max_upload_size: int = 10 * 1024 * 1024  # 10MB
    
    # Default admin credentials (for initial setup)
    default_admin_username: str = "admin"
    default_admin_password: str = "admin123"
    
    # Debug settings
    debug_mode: bool = False
    mqtt_debug: bool = True
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    @field_validator("database_url", mode="before")
    @classmethod
    def fix_postgres_url(cls, v: str) -> str:
        if v and v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql://", 1)
        return v


# Global settings instance
settings = Settings()
