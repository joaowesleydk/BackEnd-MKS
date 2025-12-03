from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)

# Config
SECRET_KEY = os.getenv('SECRET_KEY', 'mks-store-secret-key-2024-super-secure')
DATABASE_URL = os.getenv('DATABASE_URL')

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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port)