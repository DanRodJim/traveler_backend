from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    PROJECT_NAME: str = "Travel Planner API"
    VERSION: str = "1.0.0"
    ENV: str = "development"
    
    DATABASE_URL: str
    
    FRONTEND_URL: str
    ALLOWED_ORIGINS: List[str] = []
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def is_production(self) -> bool:
        return self.ENV == "production"
    
    def is_development(self) -> bool:
        return self.ENV == "development"

    def is_testing(self) -> bool:
        return self.ENV.lower() == "test"
    
    def get_log_level(self) -> str:
        if self.is_production():
            return "INFO"
        elif self.is_testing():
            return "WARNING"
        else:
            return "DEBUG"
    
    def should_show_docs(self) -> bool:
        return not self.is_production()
    
    def get_cors_origins(self) -> List[str]:
        if self.is_production():
            return self.ALLOWED_ORIGINS
        else:
            return ["*"]
        
settings = Settings()  # type: ignore[call-arg]