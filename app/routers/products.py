from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.product import Product
from app.auth import require_admin

router = APIRouter(prefix="/products", tags=["Products"])

class ProductCreate(BaseModel):
    nome: str
    descricao: str = None
    preco: float
    imagens: List[str] = []
    categoria: str
    promocao: bool = False
    preco_promocional: float = None
    estoque: int = 0

class ProductUpdate(BaseModel):
    nome: str = None
    descricao: str = None
    preco: float = None
    imagens: List[str] = None
    categoria: str = None
    promocao: bool = None
    preco_promocional: float = None
    estoque: int = None

@router.get("/")
def get_products(
    categoria: Optional[str] = None,
    search: Optional[str] = None,
    promocao: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Product).filter(Product.is_active == True)
    
    if categoria:
        query = query.filter(Product.categoria == categoria)
    
    if search:
        query = query.filter(or_(
            Product.nome.ilike(f"%{search}%"),
            Product.descricao.ilike(f"%{search}%")
        ))
    
    if promocao is not None:
        query = query.filter(Product.promocao == promocao)
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/categories")
def get_categories():
    return ["Feminina", "Masculina", "Cosméticos", "Bijuterias"]

@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", dependencies=[Depends(require_admin)])
def create_product(product_data: ProductCreate, db: Session = Depends(get_db)):
    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

@router.put("/{product_id}", dependencies=[Depends(require_admin)])
def update_product(product_id: int, product_data: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for field, value in product_data.dict(exclude_unset=True).items():
        setattr(product, field, value)
    
    db.commit()
    return product

@router.delete("/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = False
    db.commit()
    return {"message": "Product deleted successfully"}