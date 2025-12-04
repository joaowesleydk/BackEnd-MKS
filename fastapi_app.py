from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import hashlib
import jwt
import os
from datetime import datetime, timedelta
import requests

app = FastAPI(title="MKS Store API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Config
SECRET_KEY = os.getenv('SECRET_KEY', 'mks-store-secret-key-2024-super-secure')
MERCADOPAGO_ACCESS_TOKEN = os.getenv('MERCADOPAGO_ACCESS_TOKEN')

# Schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str

class ProductCreate(BaseModel):
    name: str
    price: float
    description: str = ""
    image_url: str = ""

class PaymentRequest(BaseModel):
    items: list

# Database setup
def init_db():
    conn = sqlite3.connect('mks_store.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def create_token(email: str) -> str:
    payload = {
        'email': email,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

@app.get("/")
def root():
    return {"message": "MKS Store API - FastAPI"}

@app.post("/api/auth/login")
def login(login_data: LoginRequest):
    conn = sqlite3.connect('mks_store.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = ?", (login_data.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or user[3] != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = create_token(login_data.email)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/register")
def register(user_data: UserCreate):
    conn = sqlite3.connect('mks_store.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (?, ?, ?)",
            (user_data.email, user_data.name, hash_password(user_data.password))
        )
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Usuário criado: {user_data.email}"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email já cadastrado")

@app.post("/api/products/frontend-create")
def create_product(product_data: ProductCreate):
    conn = sqlite3.connect('mks_store.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO products (name, price, description, image_url) VALUES (?, ?, ?, ?)",
        (product_data.name, product_data.price, product_data.description, product_data.image_url)
    )
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    
    return {
        "success": True,
        "message": "Produto criado com sucesso",
        "product": {
            "id": product_id,
            "name": product_data.name,
            "price": product_data.price
        }
    }

@app.get("/api/products/frontend")
def list_products():
    conn = sqlite3.connect('mks_store.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
    products = cursor.fetchall()
    conn.close()
    
    return {
        "products": [
            {
                "id": p[0],
                "name": p[1],
                "price": p[2],
                "description": p[3],
                "image_url": p[4],
                "created_at": p[5]
            } for p in products
        ]
    }

@app.post("/api/payments/create-preference")
def create_preference(payment_data: PaymentRequest):
    try:
        preference_data = {
            "items": [
                {
                    "title": item.get('title', 'Produto'),
                    "quantity": item.get('quantity', 1),
                    "unit_price": float(item.get('price', 0))
                } for item in payment_data.items
            ],
            "back_urls": {
                "success": "https://modakarinastore.com.br/success",
                "failure": "https://modakarinastore.com.br/failure",
                "pending": "https://modakarinastore.com.br/pending"
            },
            "auto_return": "approved"
        }
        
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
            raise HTTPException(status_code=400, detail="Erro ao criar preferência")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))