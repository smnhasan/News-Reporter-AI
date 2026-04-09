from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "News Reporter AI"
    MONGODB_URL: str = os.getenv("MONGODB_URL", "")
    DATABASE_NAME: str = "news_reporter_ai"
    
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60 * 24))

    class Config:
        case_sensitive = True

settings = Settings()
