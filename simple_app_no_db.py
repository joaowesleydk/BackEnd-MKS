from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app)

# Config
SECRET_KEY = os.getenv('SECRET_KEY', 'mks-store-secret-key-2024-super-secure')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN')

@app.route('/')
def home():
    return {"message": "MKS Store API - Flask"}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return {"error": "Email e senha são obrigatórios"}, 400
    
    # Mock login - sempre retorna sucesso para teste
    return {
        "access_token": "mock_token_123",
        "token_type": "bearer"
    }

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not email or not name or not password:
        return {"error": "Email, nome e senha são obrigatórios"}, 400
    
    # Mock register - sempre retorna sucesso para teste
    return {"success": True, "message": f"Usuário criado: {email}"}

@app.route('/api/payments/create-preference', methods=['POST'])
def create_preference():
    data = request.get_json()
    items = data.get('items', [])
    
    if not items:
        return {"error": "Items são obrigatórios"}, 400
    
    try:
        # Monta preferência do Mercado Pago
        preference_data = {
            "items": [
                {
                    "title": item.get('title', 'Produto'),
                    "quantity": item.get('quantity', 1),
                    "unit_price": float(item.get('price', 0))
                } for item in items
            ],
            "back_urls": {
                "success": "https://seu-frontend.com/success",
                "failure": "https://seu-frontend.com/failure",
                "pending": "https://seu-frontend.com/pending"
            },
            "auto_return": "approved"
        }
        
        # Faz requisição para API do Mercado Pago
        headers = {
            "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            "https://api.mercadopago.com/checkout/preferences",
            json=preference_data,
            headers=headers
        )
        
        if response.status_code == 201:
            preference = response.json()
            return {
                "id": preference["id"],
                "init_point": preference["init_point"],
                "sandbox_init_point": preference["sandbox_init_point"]
            }
        else:
            return {"error": "Erro ao criar preferência", "details": response.text}, 400
            
    except Exception as e:
        return {"error": str(e)}, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)