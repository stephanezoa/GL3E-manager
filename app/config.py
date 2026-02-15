"""
Configuration management for GL3E Project Assignment System
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "GL3E Project Assignment"
    SECRET_KEY: str
    DEBUG: bool = False
    DOMAIN: str = "stephanezoa.online"
    
    # Database
    DATABASE_URL: str = "sqlite:///./gl3e_assignments.db"
    
    # Email Configuration
    SMTP_HOST: str
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM: str
    SMTP_USE_TLS: bool = True
    
    # SMS Configuration - mTarget (Primary)
    MTARGET_USERNAME: str
    MTARGET_PASSWORD: str
    MTARGET_SERVICE_ID: str
    MTARGET_SENDER: str = "FM OTP"
    MTARGET_API_URL: str = "https://api-public-2.mtarget.fr/messages"
    
    # SMS Configuration - Twilio (Fallback)
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str
    
    # OTP Configuration
    OTP_LENGTH: int = 6
    OTP_EXPIRY_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
