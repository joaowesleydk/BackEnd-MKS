# app/main.py
# -----------
# Ponto de entrada da aplicação FastAPI
from fastapi import FastAPI
from app.core.database import Base, engine
from app.routers import products, auth

# Cria as tabelas no banco (apenas para dev com sqlite).
# Em produção você usará Alembic para migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="E-commerce Minimal - FastAPI")

# Inclui os routers
app.include_router(auth.router)
app.include_router(products.router)

@app.get("/health")
def health():
    return {"status": "ok"}
