from typing import List
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from uuid import uuid4
import os
import shutil
from app.core.database import get_db
from app.crud.crud import get_products, get_product, create_product, get_categories, create_category
from app.schemas.schemas import Product, ProductCreate, Category, CategoryCreate, User
from app.api.routes.auth import get_admin_user

router = APIRouter()

# ============================================================================
# ENDPOINTS PARA FRONTEND (formato específico)
# ============================================================================

@router.get("/frontend")
def get_products_frontend(
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None,
    db: Session = Depends(get_db)
):
    """Retorna produtos no formato para o frontend"""
    products = get_products(db, skip=skip, limit=limit, category_id=category_id)
    
    return [
        {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        for product in products
    ]

@router.get("/categoria/{categoria_nome}")
def get_products_by_category(categoria_nome: str, db: Session = Depends(get_db)):
    """Busca produtos por categoria (formato frontend)"""
    from app.models.models import Category
    
    category = db.query(Category).filter(Category.name.ilike(f"%{categoria_nome}%")).first()
    if not category:
        return []
    
    products = get_products(db, category_id=category.id)
    
    return [
        {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        for product in products
    ]

@router.get("/search")
def search_products(q: str, db: Session = Depends(get_db)):
    """Busca produtos por termo (formato frontend)"""
    if not q or len(q.strip()) < 2:
        return []
    
    products = get_products(db, search=q.strip())
    
    return [
        {
            "nome": product.name,
            "preco": f"R$ {product.price:.2f}".replace(".", ","),
            "imagem": product.image_url or "https://via.placeholder.com/300x300?text=Sem+Imagem",
            "categoria": product.category.name.lower() if product.category else "sem-categoria"
        }
        for product in products
    ]

@router.post("/frontend-create")
def create_product_frontend(
    produto: dict,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Cadastra produto via frontend"""
    try:
        from app.models.models import Category
        
        nome = produto.get('nome')
        preco = float(produto.get('preco', 0))
        categoria = produto.get('categoria')
        imagem = produto.get('imagem')
        descricao = produto.get('descricao')
        
        # Busca categoria existente
        category = None
        if categoria:
            category = db.query(Category).filter(Category.name.ilike(categoria)).first()
        
        product_data = ProductCreate(
            name=nome,
            description=descricao,
            price=preco,
            image_url=imagem,
            stock=100,
            category_id=category.id if category else None
        )
        
        new_product = create_product(db=db, product=product_data)
        
        return {
            "success": True,
            "message": "Produto cadastrado com sucesso!"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro: {str(e)}"}

@router.post("/frontend-create-with-file")
async def create_product_with_file(
    name: str = Form(...),
    price: float = Form(...),
    category: str = Form(...),
    description: str = Form(""),
    promocao: bool = Form(False),
    imagemFile: UploadFile = File(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Cadastra produto com upload de imagem"""
    try:
        # Validar arquivo de imagem
        if not imagemFile.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
        
        # Validar tamanho (máximo 5MB)
        contents = await imagemFile.read()
        if len(contents) > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="Imagem muito grande. Máximo 5MB")
        
        # Gerar nome único para o arquivo
        file_extension = imagemFile.filename.split('.')[-1] if '.' in imagemFile.filename else 'jpg'
        unique_filename = f"{uuid4()}.{file_extension}"
        
        # Salvar arquivo no diretório de uploads
        upload_dir = "uploads/products"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            buffer.write(contents)
        
        # URL da imagem para salvar no banco
        image_url = f"/uploads/products/{unique_filename}"
        
        # Buscar categoria
        from app.models.models import Category
        category_obj = None
        if category:
            category_obj = db.query(Category).filter(Category.name.ilike(category)).first()
        
        # Criar produto no banco
        product_data = ProductCreate(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            stock=100,
            category_id=category_obj.id if category_obj else None
        )
        
        new_product = create_product(db=db, product=product_data)
        
        return {
            "success": True,
            "message": "Produto criado com sucesso",
            "produto": {
                "name": name,
                "price": price,
                "category": category,
                "image": image_url,
                "description": description,
                "promocao": promocao
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Remove arquivo se houve erro
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")

# ============================================================================
# ENDPOINTS ADMINISTRATIVOS (formato padrão)
# ============================================================================

@router.get("/", response_model=List[Product])
def get_products_admin(
    skip: int = 0, 
    limit: int = 100, 
    category_id: int = None,
    min_price: float = None,
    max_price: float = None,
    search: str = None,
    db: Session = Depends(get_db)
):
    """Lista produtos (formato admin)"""
    return get_products(db, skip=skip, limit=limit, category_id=category_id, 
                       min_price=min_price, max_price=max_price, search=search)

@router.get("/{product_id}", response_model=Product)
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """Busca produto por ID"""
    product = get_product(db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    return product

@router.post("/", response_model=Product)
def create_new_product(
    product: ProductCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Cria produto (formato admin)"""
    return create_product(db=db, product=product)

@router.put("/{product_id}", response_model=Product)
def update_product(
    product_id: int,
    product: ProductCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Atualiza produto"""
    db_product = get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    for key, value in product.dict().items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Deleta produto (soft delete)"""
    db_product = get_product(db, product_id=product_id)
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Soft delete - marca como inativo
    db_product.is_active = False
    db.commit()
    
    return {"message": "Produto deletado com sucesso"}

@router.delete("/{product_id}/permanent")
def delete_product_permanent(
    product_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Deleta produto permanentemente"""
    db_product = db.query(Product).filter(Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    
    # Remove arquivo de imagem se existir
    if db_product.image_url and db_product.image_url.startswith('/uploads/'):
        file_path = db_product.image_url[1:]  # Remove a barra inicial
        if os.path.exists(file_path):
            os.remove(file_path)
    
    db.delete(db_product)
    db.commit()
    
    return {"message": "Produto deletado permanentemente"}

# ============================================================================
# ENDPOINTS DE CATEGORIAS
# ============================================================================

@router.get("/categories/", response_model=List[Category])
def get_categories_list(db: Session = Depends(get_db)):
    """Lista todas as categorias"""
    return get_categories(db)

@router.post("/categories/", response_model=Category)
def create_new_category(
    category: CategoryCreate, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Cria nova categoria"""
    return create_category(db=db, category=category)

@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    category_id: int,
    category: CategoryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Atualiza categoria"""
    from app.models.models import Category
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    for key, value in category.dict().items():
        setattr(db_category, key, value)
    
    db.commit()
    db.refresh(db_category)
    return db_category

@router.delete("/categories/{category_id}")
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """Deleta categoria"""
    from app.models.models import Category
    db_category = db.query(Category).filter(Category.id == category_id).first()
    if not db_category:
        raise HTTPException(status_code=404, detail="Categoria não encontrada")
    
    # Verifica se há produtos usando esta categoria
    products_count = db.query(Product).filter(Product.category_id == category_id, Product.is_active == True).count()
    if products_count > 0:
        raise HTTPException(status_code=400, detail=f"Não é possível deletar. Categoria possui {products_count} produtos ativos")
    
    db.delete(db_category)
    db.commit()
    
    return {"message": "Categoria deletada com sucesso"}

# ============================================================================
# ENDPOINTS PARA SERVIR IMAGENS
# ============================================================================

@router.get("/uploads/products/{filename}")
async def get_product_image(filename: str):
    """Serve arquivos de imagem dos produtos"""
    file_path = f"uploads/products/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Imagem não encontrada")
    
    return FileResponse(file_path)