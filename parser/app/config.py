from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    REDIS_URL: str = "redis://redis:6379/0"
    BACKEND_API_URL: str = "http://backend:8000/api/v1"
    
    class Config:
        env_file = ".env"

settings = Settings()
