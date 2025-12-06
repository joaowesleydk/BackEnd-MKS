import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/mks_store")
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    algorithm: str = os.getenv("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

    class Config:
        env_file = ".env"

settings = Settings()