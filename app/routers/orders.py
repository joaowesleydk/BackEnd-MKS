from fastapi import APIRouter, Depends, HTTPException
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

router = APIRouter(prefix="/orders", tags=["Orders"])

class AddressData(BaseModel):
    cep: str
    logradouro: str
    numero: str
    complemento: str = ""
    bairro: str
    cidade: str
    uf: str

class OrderCreate(BaseModel):
    endereco: AddressData
    payment_method: str = "pix"

@router.get("/")
def get_orders(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = db.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_at.desc()).all()
    return orders

@router.get("/{order_id}")
def get_order(order_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id, Order.user_id == current_user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.post("/calculate-shipping")
def calculate_shipping(cep: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Calcular total do carrinho
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    total = 0
    
    for item in cart_items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if product:
            preco_atual = product.preco_promocional if product.promocao else product.preco
            total += preco_atual * item.quantidade
    
    shipping_info = ViaCEPService.calculate_shipping(cep, total)
    return shipping_info

@router.post("/")
def create_order(order_data: OrderCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Verificar carrinho
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    # Calcular total e preparar items
    total = 0
    items = []
    
    for cart_item in cart_items:
        product = db.query(Product).filter(Product.id == cart_item.product_id).first()
        if not product or not product.is_active:
            raise HTTPException(status_code=400, detail=f"Product {cart_item.product_id} not available")
        
        if product.estoque < cart_item.quantidade:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for {product.nome}")
        
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
    
    # Calcular frete
    shipping_info = ViaCEPService.calculate_shipping(order_data.endereco.cep, total)
    frete = shipping_info["frete"]
    total_com_frete = total + frete
    
    # Criar pedido
    order = Order(
        user_id=current_user.id,
        total=total_com_frete,
        frete=frete,
        endereco=order_data.endereco.dict(),
        items=items,
        payment_method=order_data.payment_method
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    
    # Criar pagamento no Mercado Pago
    mp_service = MercadoPagoService()
    payment_response = mp_service.create_payment({
        "order_id": order.id,
        "total": total_com_frete,
        "email": current_user.email,
        "nome": current_user.nome,
        "payment_method": order_data.payment_method
    })
    
    # Atualizar pedido com payment_id
    order.payment_id = payment_response.get("id")
    db.commit()
    
    # Limpar carrinho
    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    
    return {
        "order": order,
        "payment": payment_response
    }