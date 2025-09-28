"""
Project Chimera Configuration Module
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Global configuration for Project Chimera"""
    
    # OpenRouter API Configuration
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "anthropic/claude-3-sonnet-20240229")
    
    # Simulation Configuration
    SESSION_ID = os.getenv("SESSION_ID", "chimera_simulation_001")
    TICK_DURATION = 1.0  # seconds per tick in real time
    MAX_AGENTS = 10
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_DIR = os.getenv("LOG_DIR", "./logs")
    
    # Server Configuration
    HOST = "localhost"
    PORT = 8000
    
    # Frontend Configuration
    STATIC_DIR = "./frontend/build"
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is required. Please set it in .env file.")
        
        # Create log directory if it doesn't exist
        os.makedirs(cls.LOG_DIR, exist_ok=True)