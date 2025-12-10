from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.order import Order
from app.models.product import Product
from app.services.mercadopago import MercadoPagoService

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])

@router.post("/mercadopago")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    try:
        data = await request.json()
        
        if data.get("type") == "payment":
            payment_id = data["data"]["id"]
            
            # Buscar informações do pagamento
            mp_service = MercadoPagoService()
            payment_info = mp_service.get_payment(payment_id)
            
            # Buscar pedido pelo external_reference
            order_id = payment_info.get("external_reference")
            if order_id:
                order = db.query(Order).filter(Order.id == int(order_id)).first()
                if order:
                    # Atualizar status do pedido baseado no status do pagamento
                    payment_status = payment_info.get("status")
                    
                    if payment_status == "approved":
                        order.status = "paid"
                        
                        # Reduzir estoque dos produtos
                        for item in order.items:
                            product = db.query(Product).filter(Product.id == item["product_id"]).first()
                            if product:
                                product.estoque -= item["quantidade"]
                    
                    elif payment_status == "cancelled" or payment_status == "rejected":
                        order.status = "cancelled"
                    
                    db.commit()
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error"}