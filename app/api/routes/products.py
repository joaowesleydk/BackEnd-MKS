from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.crud.crud import get_products, get_product, create_product, get_categories, create_category
from app.schemas.schemas import Product, ProductCreate, Category, CategoryCreate, User
from app.api.routes.auth import get_admin_user

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

@router.get("/frontend")
def read_products_frontend(
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None,
    db: Session = Depends(get_db)
):
    """Endpoint que retorna produtos no formato específico para o frontend"""
    products = get_products(db, skip=skip, limit=limit, category_id=category_id)
    
    # Converte para o formato esperado pelo frontend
    frontend_products = []
    for product in products:
        frontend_product = {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        frontend_products.append(frontend_product)
    
    return frontend_products

@router.get("/{product_id}", response_model=Product)
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = get_product(db, product_id=product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/", response_model=Product)
def create_new_product(
    product: ProductCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    return create_product(db=db, product=product)

@router.get("/categories/", response_model=List[Category])
def read_categories(db: Session = Depends(get_db)):
    return get_categories(db)

@router.get("/categoria/{categoria_nome}")
def read_products_by_category(
    categoria_nome: str,
    db: Session = Depends(get_db)
):
    """Endpoint para buscar produtos por categoria no formato frontend"""
    # Busca a categoria pelo nome
    from app.models.models import Category
    category = db.query(Category).filter(Category.name.ilike(f"%{categoria_nome}%")).first()
    
    if not category:
        return []
    
    # Busca produtos da categoria
    products = get_products(db, category_id=category.id)
    
    # Converte para formato frontend
    frontend_products = []
    for product in products:
        frontend_product = {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        frontend_products.append(frontend_product)
    
    return frontend_products

@router.get("/search")
def search_products(
    q: str,
    db: Session = Depends(get_db)
):
    """Endpoint de busca para a barra de pesquisa"""
    if not q or len(q.strip()) < 2:
        return []
    
    # Busca produtos pelo termo
    products = get_products(db, search=q.strip())
    
    # Converte para formato frontend
    frontend_products = []
    for product in products:
        frontend_product = {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        frontend_products.append(frontend_product)
    
    return frontend_products

@router.post("/categories/", response_model=Category)
def create_new_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    return create_category(db=db, category=category)