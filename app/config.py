"""
Application Configuration
Load settings from environment variables
"""
import os
from dotenv import load_dotenv
from functools import lru_cache

# Load environment variables from .env file
load_dotenv()


class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Supabase
        self.supabase_url = os.getenv("SUPABASE_URL", "")
        self.supabase_key = os.getenv("SUPABASE_KEY", "")
        self.supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY", "")
        
        # Application
        self.secret_key = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production-min-32-chars")
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.debug = os.getenv("DEBUG", "True").lower() == "true"
        
        # Server
        self.host = os.getenv("HOST", "0.0.0.0")
        self.port = int(os.getenv("PORT", "8000"))
        
        # Organization (single-org for now)
        self.org_name = os.getenv("ORG_NAME", "My Company")
        self.org_timezone = os.getenv("ORG_TIMEZONE", "UTC")
        self.work_start_time = os.getenv("WORK_START_TIME", "09:00")
        self.work_end_time = os.getenv("WORK_END_TIME", "17:00")


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
