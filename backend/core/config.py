from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / '.env'

class Settings(BaseSettings):
    # MongoDB
    MONGO_URL: str
    DB_NAME: str
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production-use-openssl-rand-hex-32"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OTP
    OTP_EXPIRE_MINUTES: int = 5
    OTP_MAX_ATTEMPTS: int = 3
    
    # Rate Limiting
    RATE_LIMIT_OTP_PER_HOUR: int = 5
    RATE_LIMIT_LOGIN_PER_HOUR: int = 10
    
    # CORS
    CORS_ORIGINS: str = "*"
    
    class Config:
        env_file = ENV_FILE
        case_sensitive = True

settings = Settings()