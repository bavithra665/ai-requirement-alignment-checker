from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Requirement-to-Implementation Alignment Checker"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    DATABASE_URL: str
    
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    
    # Jira Integration (optional)
    JIRA_BASE_URL: Optional[str] = None
    JIRA_API_TOKEN: Optional[str] = None
    JIRA_USER_EMAIL: Optional[str] = None
    
    # GitHub Integration (optional)
    GITHUB_TOKEN: Optional[str] = None
    
    # Groq AI
    GROQ_API_KEY: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

settings = Settings()
