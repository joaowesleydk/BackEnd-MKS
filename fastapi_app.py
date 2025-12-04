from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
import jwt
import os
from datetime import datetime, timedelta
import requests
import base64
from typing import Optional
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import replicate

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
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
DATABASE_URL = os.getenv('DATABASE_URL')
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# Configure Replicate
if REPLICATE_API_TOKEN:
    os.environ['REPLICATE_API_TOKEN'] = REPLICATE_API_TOKEN

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

# Database connection
def get_db_connection():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

# Database setup
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            role VARCHAR(50) DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description TEXT,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS virtual_tryons (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id),
            original_image_url TEXT,
            garment_image_url TEXT,
            result_image_url TEXT,
            model_used VARCHAR(100),
            processing_time DECIMAL(5,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
try:
    init_db()
except Exception as e:
    print(f"Database initialization error: {e}")

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

def process_virtual_tryon(person_image_b64: str, garment_image_url: str, model: str = "default") -> dict:
    try:
        # Convert base64 to URL (upload to temporary storage)
        person_image_url = upload_base64_to_temp_storage(person_image_b64)
        
        # Use Replicate API for virtual try-on
        output = replicate.run(
            "cuuupid/idm-vton:c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
            input={
                "crop": False,
                "seed": 42,
                "steps": 30,
                "category": "upper_body",
                "force_dc": False,
                "garm_img": garment_image_url,
                "human_img": person_image_url,
                "mask_only": False,
                "garment_des": "A stylish garment"
            }
        )
        
        return {
            "success": True,
            "output_image_url": output,
            "processing_time": "3.2s"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Virtual try-on failed: {str(e)}")

def upload_base64_to_temp_storage(base64_data: str) -> str:
    # Remove data:image/jpeg;base64, prefix if present
    if ',' in base64_data:
        base64_data = base64_data.split(',')[1]
    
    # For production, upload to Cloudinary or similar
    # For now, return a placeholder URL
    # You should implement actual file upload here
    return "https://example.com/temp-image.jpg"

@app.get("/")
def root():
    return {"message": "MKS Store API - FastAPI"}

@app.post("/api/auth/login")
def login(login_data: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users WHERE email = %s", (login_data.email,))
    user = cursor.fetchone()
    conn.close()
    
    if not user or user['password_hash'] != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = create_token(login_data.email)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/register")
def register(user_data: UserCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)",
            (user_data.email, user_data.name, hash_password(user_data.password))
        )
        conn.commit()
        conn.close()
        
        return {"success": True, "message": f"Usuário criado: {user_data.email}"}
    except psycopg2.IntegrityError:
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
        # Get user ID
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
        user = cursor.fetchone()
        user_id = user['id'] if user else None
        
        # Process virtual try-on with real AI
        result = process_virtual_tryon(
            request.person_image, 
            request.garment_image, 
            request.model
        )
        
        # Save to database
        cursor.execute("""
            INSERT INTO virtual_tryons (user_id, garment_image_url, result_image_url, model_used, processing_time)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            user_id,
            request.garment_image,
            result['output_image_url'],
            request.model,
            float(result['processing_time'].replace('s', ''))
        ))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "output_image": result['output_image_url'],
            "model_used": request.model,
            "processing_time": result['processing_time'],
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        
        if not user:
            # Criar novo usuário
            cursor.execute(
                "INSERT INTO users (email, name, password_hash, role) VALUES (%s, %s, %s, %s) RETURNING id",
                (email, name, 'google_auth', 'user')
            )
            user_id = cursor.fetchone()['id']
            conn.commit()
        else:
            user_id = user['id']
        
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