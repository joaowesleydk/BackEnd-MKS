from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
import requests

app = Flask(__name__)
CORS(app)

# Config
SECRET_KEY = os.getenv('SECRET_KEY', 'mks-store-secret-key-2024-super-secure')
DATABASE_URL = os.getenv('DATABASE_URL')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

@app.route('/')
def home():
    return {"message": "MKS Store API"}

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return {"error": "Email e senha são obrigatórios"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id, email, hashed_password FROM users WHERE email = %s", (email,))
        user = cur.fetchone()
        
        if user and check_password_hash(user[2], password):
            token = jwt.encode({
                'user_id': user[0],
                'email': user[1],
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, SECRET_KEY, algorithm='HS256')
            
            return {
                "access_token": token,
                "token_type": "bearer"
            }
        else:
            return {"error": "Email ou senha incorretos"}, 401
            
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        if conn:
            conn.close()

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    name = data.get('name')
    password = data.get('password')
    
    if not email or not name or not password:
        return {"error": "Email, nome e senha são obrigatórios"}, 400
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verifica se email existe
        cur.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cur.fetchone():
            return {"error": "Email já cadastrado"}, 400
        
        # Cria usuário
        hashed_pw = generate_password_hash(password)
        cur.execute("""
            INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
            VALUES (%s, %s, %s, 'user', true, NOW())
        """, (email, name, hashed_pw))
        
        conn.commit()
        return {"success": True, "message": f"Usuário criado: {email}"}
        
    except Exception as e:
        return {"error": str(e)}, 500
    finally:
        if conn:
            conn.close()

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