from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.routes.auth import get_current_user
from app.schemas.schemas import User
from app.core.mercadopago_config import mp
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

# Funções auxiliares
async def process_approved_payment(payment, external_reference, db):
    """Processa pagamento aprovado"""
    try:
        # Aqui você pode:
        # 1. Criar pedido no banco
        # 2. Atualizar estoque
        # 3. Enviar email de confirmação
        # 4. etc.
        
        print(f"Pagamento aprovado: {payment.get('id')} - Ref: {external_reference}")
        
        # Exemplo: extrair user_id da referência
        if external_reference and external_reference.startswith("user_"):
            parts = external_reference.split("_")
            if len(parts) >= 2:
                user_id = parts[1]
                # Processar pedido para o usuário
                
    except Exception as e:
        print(f"Erro ao processar pagamento aprovado: {str(e)}")

async def process_rejected_payment(payment, external_reference, db):
    """Processa pagamento rejeitado"""
    try:
        print(f"Pagamento rejeitado: {payment.get('id')} - Ref: {external_reference}")
        # Lógica para pagamento rejeitado
        
    except Exception as e:
        print(f"Erro ao processar pagamento rejeitado: {str(e)}")