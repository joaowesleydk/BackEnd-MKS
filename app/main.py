from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import os
from app.api.routes import products, users, orders, auth, cart, upload, payments, virtual_tryon
from app.core.database import engine
from app.models import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MKS Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(orders.router, prefix="/api/orders", tags=["orders"])
app.include_router(cart.router, prefix="/api/cart", tags=["cart"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(payments.router, prefix="/api/payments", tags=["payments"])
app.include_router(virtual_tryon.router, prefix="/api", tags=["virtual-tryon"])

# Criar diretório de uploads se não existir
os.makedirs("uploads/products", exist_ok=True)

# Servir arquivos estáticos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.get("/")
def read_root():
    return {"message": "MKS Store API"}

@app.get("/uploads/products/{filename}")
async def get_product_image(filename: str):
    """Endpoint alternativo para servir imagens de produtos"""
    file_path = f"uploads/products/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    return FileResponse(file_path)