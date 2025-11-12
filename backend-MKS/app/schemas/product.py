# app/schemas/product.py
from pydantic import BaseModel

class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    stock: int = 0

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price: float | None = None
    stock: int | None = None

class ProductOut(ProductBase):
    id: int
    class Config:
        orm_mode = True  # permite serializar ORM objects diretamente
