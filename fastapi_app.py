from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import sqlite3
import hashlib
import jwt
import os
from datetime import datetime, timedelta
import requests
import base64
import io
from PIL import Image, ImageDraw, ImageFont
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

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
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID', '1234567890-abcdefghijklmnopqrstuvwxyz.apps.googleusercontent.com')

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

class VirtualTryOnRequest(BaseModel):
    person_image: str  # base64
    garment_image: str  # URL
    model: str = "default"

class GoogleAuthRequest(BaseModel):
    credential: str  # JWT token do Google

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

def verify_token(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token não fornecido")
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload['email']
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")

def create_mock_tryon(person_b64: str, garment_url: str) -> str:
    try:
        # Decode person image
        person_data = base64.b64decode(person_b64)
        person_img = Image.open(io.BytesIO(person_data))
        
        # Create overlay effect (mock)
        draw = ImageDraw.Draw(person_img)
        width, height = person_img.size
        
        # Add semi-transparent overlay
        overlay = Image.new('RGBA', (width, height), (255, 0, 0, 50))
        person_img = Image.alpha_composite(person_img.convert('RGBA'), overlay)
        
        # Add text overlay
        try:
            font = ImageFont.load_default()
        except:
            font = None
            
        draw = ImageDraw.Draw(person_img)
        text = "Virtual Try-On Applied"
        if font:
            draw.text((10, 10), text, fill=(255, 255, 255, 255), font=font)
        else:
            draw.text((10, 10), text, fill=(255, 255, 255, 255))
        
        # Convert back to base64
        buffer = io.BytesIO()
        person_img.convert('RGB').save(buffer, format='JPEG')
        result_b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/jpeg;base64,{result_b64}"
        
    except Exception as e:
        # Fallback: return original image
        return f"data:image/jpeg;base64,{person_b64}"

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

@app.post("/api/virtual-tryon")
def virtual_tryon(request: VirtualTryOnRequest, user_email: str = Depends(verify_token)):
    try:
        # Mock virtual try-on processing
        output_image = create_mock_tryon(request.person_image, request.garment_image)
        
        return {
            "success": True,
            "output_image": output_image,
            "model_used": request.model,
            "processing_time": "2.5s",
            "user": user_email
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@app.post("/api/auth/google")
def google_auth(request: GoogleAuthRequest):
    try:
        # Validar token do Google
        idinfo = id_token.verify_oauth2_token(
            request.credential, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        # Extrair dados do usuário
        email = idinfo['email']
        name = idinfo['name']
        google_id = idinfo['sub']
        
        # Verificar se usuário já existe no banco
        conn = sqlite3.connect('mks_store.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        
        if not user:
            # Criar novo usuário
            cursor.execute(
                "INSERT INTO users (email, name, password_hash, role) VALUES (?, ?, ?, ?)",
                (email, name, 'google_auth', 'user')
            )
            conn.commit()
            user_id = cursor.lastrowid
        else:
            user_id = user[0]
        
        conn.close()
        
        # Criar token JWT próprio
        access_token = create_token(email)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": email,
                "name": name,
                "role": "user"
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=401, detail="Token do Google inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na autenticação: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))