from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from app.database import Base, engine
from app.routers import auth, produtos, carrinho, usuario, pagamento, cep, frete, webhook
from app.routers.produtos import products_router
import os
from dotenv import load_dotenv

load_dotenv()

# Criar tabelas apenas se não estiver em produção
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Warning: Could not create tables: {e}")

app = FastAPI(
    title="Moda Karina Store API",
    description="Backend completo para e-commerce de moda",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://karinamodastore.com.br",
        "https://www.modakarinastore.com.br",
        "https://modakarinastore.com.br",
        "http://localhost:5173",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Health check
@app.get("/")
def health_check():
    return {"message": "Moda Karina Store API is running!", "version": "1.0.0"}

# Routers
app.include_router(auth.router, prefix="/api")
app.include_router(produtos.router, prefix="/api")
app.include_router(products_router, prefix="/api")
app.include_router(carrinho.router, prefix="/api")
app.include_router(usuario.router, prefix="/api")
app.include_router(pagamento.router, prefix="/api")
app.include_router(cep.router, prefix="/api")
app.include_router(frete.router, prefix="/api")
app.include_router(webhook.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)