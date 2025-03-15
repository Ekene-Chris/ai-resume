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
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    
    # Azure OpenAI settings
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    
    # Azure Document Intelligence settings
    DOCUMENT_INTELLIGENCE_ENDPOINT: str = ""
    DOCUMENT_INTELLIGENCE_KEY: str = ""
    DOCUMENT_INTELLIGENCE_MODEL_ID: str = "prebuilt-document"  # or "prebuilt-layout" or "prebuilt-read"
    
    # Azure Cosmos DB settings
    COSMOS_DB_ENDPOINT: str = ""
    COSMOS_DB_KEY: str = ""
    COSMOS_DB_DATABASE: str = "resume-analyzer"
    COSMOS_DB_ANALYSES_CONTAINER: str = "analyses"
    
    # Application URLs
    APP_FRONTEND_URL: str = "http://localhost:3000"  # Frontend URL for email links
    
    # Azure Communication Services (Email) settings
    EMAIL_ENABLED: bool = False
    AZURE_COMMUNICATION_SERVICES_CONNECTION_STRING: str = ""
    EMAIL_SENDER_ADDRESS: str = "DoNotReply@teleios-resume-analyzer.azurecomm.net"

    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]  # In production, specify your frontend domain
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()