# app/core/database.py
# --------------------
# Configura conexão com o banco usando SQLAlchemy (sync)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

# Cria engine a partir da URL (sqlite ou postgres)
# Para sqlite precisamos do check_same_thread
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(settings.database_url, connect_args=connect_args)

# Session local factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para declarar modelos
Base = declarative_base()

# Dependency do FastAPI para abrir e fechar sessão por request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
