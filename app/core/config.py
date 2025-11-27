from pydantic import BaseSettings

class Settings(BaseSettings):
    database_url: str = "postgresql://user:password@localhost/mks_store"
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    class Config:
        env_file = ".env"

settings = Settings()