import mercadopago
import os
from typing import Dict, Any

class MercadoPagoService:
    def __init__(self):
        self.sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))
    
    def create_payment(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        payment_data = {
            "transaction_amount": order_data["total"],
            "description": f"Pedido Moda Karina Store #{order_data['order_id']}",
            "payment_method_id": order_data.get("payment_method", "pix"),
            "payer": {
                "email": order_data["email"],
                "first_name": order_data["nome"]
            },
            "external_reference": str(order_data["order_id"]),
            "notification_url": "https://backend-mks-1.onrender.com/webhooks/mercadopago"
        }
        
        if order_data.get("payment_method") == "pix":
            payment_data["payment_method_id"] = "pix"
        
        payment_response = self.sdk.payment().create(payment_data)
        return payment_response["response"]
    
    def get_payment(self, payment_id: str) -> Dict[str, Any]:
        payment_response = self.sdk.payment().get(payment_id)
        return payment_response["response"]