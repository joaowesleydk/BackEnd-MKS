# app/core/config.py
# ------------------
# Configurações carregadas do .env usando Pydantic BaseSettings
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Pegamos as variáveis de ambiente do .env
    database_url: str
    secret_key: str
    access_token_expire_minutes: int = 60

    class Config:
        env_file = ".env"  # arquivo padrão com variáveis

# Instância global com as configurações
settings = Settings()
