from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Auth0 Configuration
    AUTH0_DOMAIN: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str
    AUTH0_AUDIENCE: str
    AUTH0_ALGORITHMS: List[str] = ["RS256"]
    AUTH0_VERIFY_SIGNATURE: bool = False  # Set to True in production
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_KEY: str
    
    # Application Configuration
    DEBUG: bool = True
    CORS_ALLOWED_ORIGINS: str = "*"
    ALLOWED_HOSTS: str = "localhost"
    
    # Redis Configuration (optional - for rate limiting)
    REDIS_URL: str = ""

    # OpenAI Configuration
    OPENAI_API_KEY: str
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Azure Search Configuration
    AZURE_SEARCH_ENDPOINT: str
    AZURE_SEARCH_KEY: str
    AZURE_SEARCH_INDEX_NAME: str = "roles-index"
    
    @property
    def AUTH0_ISSUER(self) -> str:
        return f"https://{self.AUTH0_DOMAIN}/"
    
    @property
    def cors_origins(self) -> List[str]:
        if self.CORS_ALLOWED_ORIGINS == "*":
            return ["*"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields from .env

settings = Settings()