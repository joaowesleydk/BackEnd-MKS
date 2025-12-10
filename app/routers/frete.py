from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
from app.database import get_db
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.auth import get_current_user
from app.services.viacep import ViaCEPService
from app.utils import success_response, error_response

router = APIRouter(prefix="/frete", tags=["Frete"])

class FreteCalcular(BaseModel):
    cep: str

@router.post("/calcular")
def calcular_frete(
    frete_data: FreteCalcular, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Calcular total do carrinho
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    
    if not cart_items:
        return error_response("Carrinho vazio", 400)
    
    total = 0
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            preco_atual = product.preco_promocional if product.promocao else product.preco
            total += preco_atual * item.quantidade
    
    shipping_info = ViaCEPService.calculate_shipping(frete_data.cep, total)
    
    return success_response(
        data=shipping_info, 
        message="Frete calculado com sucesso"
    )