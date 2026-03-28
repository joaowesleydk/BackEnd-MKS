from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Configurar SSL para PostgreSQL no Render
if DATABASE_URL and "render.com" in DATABASE_URL:
    # Adicionar parâmetros SSL para Render
    if "?" not in DATABASE_URL:
        DATABASE_URL += "?sslmode=require"
    else:
        DATABASE_URL += "&sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10
    } if DATABASE_URL and "render.com" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()