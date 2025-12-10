from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.auth import get_current_user

router = APIRouter(prefix="/cart", tags=["Cart"])

class CartItemAdd(BaseModel):
    product_id: int
    quantidade: int = 1

@router.get("/")
def get_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
                "product": {
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
    
    return {"items": cart_data, "total": total}

@router.post("/add")
def add_to_cart(item_data: CartItemAdd, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == item_data.product_id, Product.is_active == True).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product.estoque < item_data.quantidade:
        raise HTTPException(status_code=400, detail="Insufficient stock")
    
    existing_item = db.query(CartItem).filter(
        CartItem.user_id == current_user.id,
        CartItem.product_id == item_data.product_id
    ).first()
    
    if existing_item:
        existing_item.quantidade += item_data.quantidade
    else:
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=item_data.product_id,
            quantidade=item_data.quantidade
        )
        db.add(cart_item)
    
    db.commit()
    return {"message": "Item added to cart"}

@router.put("/{item_id}")
def update_cart_item(item_id: int, quantidade: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    if quantidade <= 0:
        db.delete(cart_item)
    else:
        cart_item.quantidade = quantidade
    
    db.commit()
    return {"message": "Cart updated"}

@router.delete("/{item_id}")
def remove_from_cart(item_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_item = db.query(CartItem).filter(
        CartItem.id == item_id,
        CartItem.user_id == current_user.id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}

@router.delete("/")
def clear_cart(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    return {"message": "Cart cleared"}