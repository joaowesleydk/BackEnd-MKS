import mercadopago
import os
from app.core.config import settings

# Configuração do Mercado Pago
def get_mp_client():
    """Retorna cliente configurado do Mercado Pago"""
    access_token = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not access_token:
        raise ValueError("MERCADOPAGO_ACCESS_TOKEN não configurado")
    
    sdk = mercadopago.SDK(access_token)
    return sdk

# Cliente global
mp = get_mp_client()