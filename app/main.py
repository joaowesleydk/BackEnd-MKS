from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import products, users, orders, auth
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

@app.get("/")
def read_root():
    return {"message": "MKS Store API"}