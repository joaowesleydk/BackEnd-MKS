from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Dict, Any
from app.database import get_db
from app.models.order import Order
from app.models.cart import CartItem
from app.models.product import Product
from app.models.user import User
from app.auth import get_current_user
from app.services.mercadopago import MercadoPagoService
from app.services.viacep import ViaCEPService
from app.utils import success_response, error_response

router = APIRouter(prefix="/pagamento", tags=["Pagamento"])

class EnderecoData(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cidade: str
    uf: str

class PagamentoData(BaseModel):
    endereco: EnderecoData
    frete: float
    payment_method: str = "pix"

@router.post("/mercadopago")
def criar_pagamento_mercadopago(
    payment_data: PagamentoData, 
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # Verificar carrinho
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        return error_response("Carrinho vazio", 400)
    
    # Calcular total e preparar items
    total = 0
    items = []
    
    for cart_item in cart_items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product or not product.is_active:
            return error_response(f"Produto {cart_item.product_id} não disponível", 400)
        
        if product.estoque < cart_item.quantidade:
            return error_response(f"Estoque insuficiente para {product.nome}", 400)
        
        preco_atual = product.preco_promocional if product.promocao else product.preco
        subtotal = preco_atual * cart_item.quantidade
        total += subtotal
        
        items.append({
            "product_id": product.id,
            "nome": product.nome,
            "preco": preco_atual,
            "quantidade": cart_item.quantidade,
            "subtotal": subtotal
        })
    
    total_com_frete = total + payment_data.frete
    
    # Criar pedido
    order = Order(
        user_id=current_user.id,
        total=total_com_frete,
        frete=payment_data.frete,
        endereco=payment_data.endereco.dict(),
        items=items,
        payment_method=payment_data.payment_method
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Criar pagamento no Mercado Pago
    try:
        mp_service = MercadoPagoService()
        payment_response = mp_service.create_payment({
            "order_id": order.id,
            "total": total_com_frete,
            "email": current_user.email,
            "nome": current_user.nome,
            "payment_method": payment_data.payment_method
        })
        
        # Atualizar pedido com payment_id
        order.payment_id = payment_response.get("id")
        db.commit()
        
        # Limpar carrinho
        db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
        db.commit()
        
        return success_response(
            data={
                "order_id": order.id,
                "payment": payment_response
            },
            message="Pagamento criado com sucesso"
        )
    
    except Exception as e:
        return error_response(f"Erro ao criar pagamento: {str(e)}", 500)