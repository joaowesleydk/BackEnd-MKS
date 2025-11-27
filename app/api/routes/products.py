from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.crud import get_products, get_product, create_product, get_categories, create_category
from app.schemas.schemas import Product, ProductCreate, Category, CategoryCreate

router = APIRouter()

@router.get("/", response_model=List[Product])
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    products = get_products(db, skip=skip, limit=limit, category_id=category_id, min_price=min_price, max_price=max_price, search=search)
    return products

@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=Product)
def create_new_product(product: ProductCreate, db: Session = Depends(get_db)):
    return create_product(db=db, product=product)

@router.get("/categories/", response_model=List[Category])
def read_categories(db: Session = Depends(get_db)):
    return get_categories(db)

@router.post("/categories/", response_model=Category)
def create_new_category(category: CategoryCreate, db: Session = Depends(get_db)):
    return create_category(db=db, category=category)