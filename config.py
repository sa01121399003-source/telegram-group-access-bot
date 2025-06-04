import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # ChatGPT Configuration
    CHATGPT_API_KEY = os.getenv("CHATGPT_API_KEY")
    CHATGPT_ASSISTANT_ID = os.getenv("CHATGPT_ASSISTANT_ID")
    
    # PostgreSQL Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_POOL_MIN_SIZE = int(os.getenv("DB_POOL_MIN_SIZE", "5"))
    DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))
    
    # Application Settings
    MIN_REQUIRED_USERS = 1
    MAX_REQUIRED_USERS = 20
    DEFAULT_REQUIRED_USERS = 5
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        required_vars = [
            "TELEGRAM_BOT_TOKEN",
            "CHATGPT_API_KEY", 
            "CHATGPT_ASSISTANT_ID",
            "DATABASE_URL"
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(cls, var):
                missing_vars.append(var)
        
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return True