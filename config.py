import os
from typing import Optional

class Config:
    """Configuration class for the Discord bot"""
    
    # Bot configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "your_bot_token_here")
    COMMAND_PREFIX: str = os.getenv("COMMAND_PREFIX", "!")
    
    # Web application configuration
    SESSION_SECRET: str = os.getenv("SESSION_SECRET", "default_session_secret_change_in_production")
    
    # Database configuration - Use persistent storage on Fly.io
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "/data/points.db" if os.path.exists("/data") else "points.db")
    
    # Bot settings
    MAX_POINTS_PER_TRANSACTION: int = int(os.getenv("MAX_POINTS_PER_TRANSACTION", "1000000"))
    MAX_TOTAL_POINTS: int = int(os.getenv("MAX_TOTAL_POINTS", "10000000"))
    DEFAULT_LEADERBOARD_LIMIT: int = int(os.getenv("DEFAULT_LEADERBOARD_LIMIT", "10"))
    MAX_LEADERBOARD_LIMIT: int = int(os.getenv("MAX_LEADERBOARD_LIMIT", "25"))
    
    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "bot.log")
    
    # Feature flags
    ENABLE_BACKUP: bool = os.getenv("ENABLE_BACKUP", "true").lower() == "true"
    BACKUP_INTERVAL_HOURS: int = int(os.getenv("BACKUP_INTERVAL_HOURS", "24"))
    
    @classmethod
    def validate(cls) -> bool:
        """Validate configuration settings"""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "your_bot_token_here":
            return False
            
        if cls.MAX_POINTS_PER_TRANSACTION <= 0:
            return False
            
        if cls.MAX_TOTAL_POINTS <= 0:
            return False
            
        return True
        
    @classmethod
    def get_missing_vars(cls) -> list:
        """Get list of missing required environment variables"""
        missing = []
        
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == "your_bot_token_here":
            missing.append("BOT_TOKEN")
        
        if not cls.SESSION_SECRET or cls.SESSION_SECRET == "default_session_secret_change_in_production":
            missing.append("SESSION_SECRET (recommended for production)")
            
        return missing
