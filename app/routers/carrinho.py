from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.auth import get_current_user
from app.utils import success_response, error_response

router = APIRouter(prefix="/carrinho", tags=["Carrinho"])

class CartItemAdd(BaseModel):
    produto_id: int
    quantidade: int = 1

@router.get("/")
def get_carrinho(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    
    cart_data = []
    total = 0
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product and product.is_active:
            preco_atual = product.preco_promocional if product.promocao else product.preco
            subtotal = preco_atual * item.quantidade
            total += subtotal
            
            cart_data.append({
                "id": item.id,
                "produto": {
                    "id": product.id,
                    "nome": product.nome,
                    "preco": product.preco,
                    "preco_promocional": product.preco_promocional,
                    "promocao": product.promocao,
                    "imagens": product.imagens,
                    "estoque": product.estoque
                },
                "quantidade": item.quantidade,
                "subtotal": subtotal
            })
    
    return success_response(data={"items": cart_data, "total": total}, message="Carrinho carregado")

@router.post("/adicionar")
def adicionar_carrinho(item_data: CartItemAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item_data.produto_id, Product.is_active == True).first()
    if not product:
        return error_response("Produto não encontrado", 404)
    
    if product.estoque < item_data.quantidade:
        return error_response("Estoque insuficiente", 400)
    
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.produto_id
    ).first()
    
    if existing_item:
        existing_item.quantidade += item_data.quantidade
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item_data.produto_id,
            quantidade=item_data.quantidade
        )
        db.add(cart_item)
    
    db.commit()
    return success_response(message="Item adicionado ao carrinho")

@router.put("/item/{item_id}")
def update_carrinho_item(item_id: int, quantidade: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        return error_response("Item não encontrado", 404)
    
    if quantidade <= 0:
        db.delete(cart_item)
    else:
        cart_item.quantidade = quantidade
    
    db.commit()
    return success_response(message="Carrinho atualizado")

@router.delete("/item/{item_id}")
def remover_carrinho_item(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        return error_response("Item não encontrado", 404)
    
    db.delete(cart_item)
    db.commit()
    return success_response(message="Item removido do carrinho")

@router.delete("/limpar")
def limpar_carrinho(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return success_response(message="Carrinho limpo")