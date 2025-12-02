from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.schemas.schemas import User
from app.core.mercadopago_config import get_mp
import os

router = APIRouter()

@router.post("/create-preference")
def create_payment_preference(
    preference_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cria preferência de pagamento no Mercado Pago"""
    try:
        # Monta preferência igual ao Node.js
        preference = {
            "items": preference_data.get("items", []),
            "payer": preference_data.get("payer", {}),
            "payment_methods": preference_data.get("payment_methods", {}),
            "back_urls": preference_data.get("back_urls", {}),
            "auto_return": preference_data.get("auto_return", "approved"),
            "external_reference": preference_data.get("external_reference", f"user_{current_user.id}")
        }
        
        # Cria preferência
        mp = get_mp()
        response = mp.preference().create(preference)
        
        return {
            "id": response["response"]["id"],
            "init_point": response["response"]["init_point"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook para receber notificações do Mercado Pago"""
    try:
        body = await request.json()
        webhook_type = body.get("type")
        data = body.get("data", {})
        
        if webhook_type == "payment":
            payment_id = data.get("id")
            
            if payment_id:
                # Busca pagamento igual ao Node.js
                mp = get_mp()
                payment_response = mp.payment().get(payment_id)
                payment = payment_response["response"]
                
                # Salvar no banco de dados
                # Atualizar status do pedido
                # Enviar email de confirmação
                
                print("Pagamento:", payment)
        
        return "OK"
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/payment-status/{payment_id}")
def get_payment_status(payment_id: str):
    """Consulta status de um pagamento"""
    try:
        mp = get_mp()
        payment_response = mp.payment().get(payment_id)
        payment = payment_response["response"]
        
        return {
            "id": payment.get("id"),
            "status": payment.get("status"),
            "status_detail": payment.get("status_detail"),
            "transaction_amount": payment.get("transaction_amount"),
            "external_reference": payment.get("external_reference")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar pagamento: {str(e)}")