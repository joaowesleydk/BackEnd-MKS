from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Configurar SSL para PostgreSQL no Render
if DATABASE_URL:
    # Se a URL já tem parâmetros SSL, não adicionar novamente
    if "sslmode" not in DATABASE_URL:
        if "?" in DATABASE_URL:
            DATABASE_URL += "&sslmode=require"
        else:
            DATABASE_URL += "?sslmode=require"

# Configurações específicas para Render PostgreSQL
connect_args = {}
if DATABASE_URL and "render.com" in DATABASE_URL:
    connect_args = {
        "sslmode": "require",
        "connect_timeout": 30,
        "application_name": "moda_karina_store"
    }

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=3600,  # 1 hora
    pool_size=5,
    max_overflow=10,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()