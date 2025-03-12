import os
from typing import Optional, List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings(BaseSettings):
    """Application settings."""
    
    # API settings
    api_title: str = "LLM Agent Server"
    api_description: str = "A simple API for interacting with LLM agents"
    api_version: str = "0.1.0"
    
    # Server settings
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    
    # OpenAI settings
    openai_api_key: SecretStr = Field(default=SecretStr(os.environ.get("OPENAI_API_KEY", "")), description="OpenAI API key")
    
    # Optional SerpAPI key for search functionality
    serpapi_api_key: Optional[SecretStr] = Field(default=SecretStr(os.environ.get("SERPAPI_API_KEY", "")) if os.environ.get("SERPAPI_API_KEY") else None, description="SerpAPI key for Google search")
    
    # Agent settings
    default_model: str = "gpt-4o"
    available_models: List[str] = ["gpt-3.5-turbo", "gpt-4o", "gpt-4-turbo"]
    
    # Logging settings
    log_level: str = "INFO"
    
    # Vector database settings
    vector_db_path: str = "./vector_db"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="APP_",
        case_sensitive=False,
    )
    
    def model_post_init(self, __context):
        """Set environment variables for libraries that expect them directly."""
        # Set OPENAI_API_KEY for the llm_agents library
        os.environ["OPENAI_API_KEY"] = self.openai_api_key.get_secret_value()
        
        # Set SERPAPI_API_KEY for the llm_agents library if provided
        if self.serpapi_api_key:
            os.environ["SERPAPI_API_KEY"] = self.serpapi_api_key.get_secret_value()


def get_settings() -> Settings:
    """Get application settings."""
    return Settings() 