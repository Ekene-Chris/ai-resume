# app/config.py
from pydantic_settings import BaseSettings
import os
from functools import lru_cache

class Settings(BaseSettings):
    # Application information
    APP_NAME: str = "AI Resume Analyzer"
    API_VERSION: str = "v1"
    
    # Azure Blob Storage settings
    AZURE_STORAGE_ACCOUNT_NAME: str  # Add this new setting
    AZURE_STORAGE_CONTAINER_NAME: str = "cv-uploads"
    
    # Keep the connection string for backward compatibility
    # This won't be used in the updated code
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    
    # Azure OpenAI settings
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    
    # Azure Cosmos DB settings
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_KEY: str = ""
    COSMOS_DB_DATABASE: str = "resume-analyzer"
    COSMOS_DB_ANALYSES_CONTAINER: str = "analyses"
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]  # In production, specify your frontend domain
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()