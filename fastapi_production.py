from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import asyncpg
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
    person_image: str
    garment_image: str
    model: str = "default"

class GoogleAuthRequest(BaseModel):
    credential: str

# Database
async def get_db():
    return await asyncpg.connect(DATABASE_URL)

@app.on_event("startup")
async def startup():
    try:
        conn = await get_db()
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                description TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS virtual_tryons (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                garment_image_url TEXT,
                result_image_url TEXT,
                model_used VARCHAR(100),
                processing_time DECIMAL(5,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        await conn.close()
    except Exception as e:
        print(f"Database error: {e}")

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

async def process_virtual_tryon(person_image_b64: str, garment_image_url: str, model: str = "default") -> dict:
    try:
        # Upload base64 to temporary storage (implement with Cloudinary)
        person_image_url = await upload_base64_to_cloudinary(person_image_b64)
        
        # Use Replicate API
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

async def upload_base64_to_cloudinary(base64_data: str) -> str:
    import cloudinary
    import cloudinary.uploader
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    try:
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(f"data:image/jpeg;base64,{base64_data}")
        return result['secure_url']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.get("/")
def root():
    return {"message": "MKS Store API - Production"}

@app.post("/api/auth/login")
async def login(login_data: LoginRequest):
    conn = await get_db()
    user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", login_data.email)
    await conn.close()
    
    if not user or user['password_hash'] != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    token = create_token(login_data.email)
    return {"access_token": token, "token_type": "bearer"}

@app.post("/api/auth/register")
async def register(user_data: UserCreate):
    conn = await get_db()
    
    try:
        await conn.execute(
            "INSERT INTO users (email, name, password_hash) VALUES ($1, $2, $3)",
            user_data.email, user_data.name, hash_password(user_data.password)
        )
        await conn.close()
        return {"success": True, "message": f"Usuário criado: {user_data.email}"}
    except asyncpg.UniqueViolationError:
        await conn.close()
        raise HTTPException(status_code=400, detail="Email já cadastrado")

@app.post("/api/auth/google")
async def google_auth(request: GoogleAuthRequest):
    try:
        idinfo = id_token.verify_oauth2_token(
            request.credential, 
            google_requests.Request(), 
            GOOGLE_CLIENT_ID
        )
        
        email = idinfo['email']
        name = idinfo['name']
        
        conn = await get_db()
        user = await conn.fetchrow("SELECT * FROM users WHERE email = $1", email)
        
        if not user:
            user_id = await conn.fetchval(
                "INSERT INTO users (email, name, password_hash, role) VALUES ($1, $2, $3, $4) RETURNING id",
                email, name, 'google_auth', 'user'
            )
        else:
            user_id = user['id']
        
        await conn.close()
        
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
        
    except ValueError:
        raise HTTPException(status_code=401, detail="Token do Google inválido")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na autenticação: {str(e)}")

@app.post("/api/products/frontend-create")
async def create_product(product_data: ProductCreate):
    conn = await get_db()
    
    product_id = await conn.fetchval(
        "INSERT INTO products (name, price, description, image_url) VALUES ($1, $2, $3, $4) RETURNING id",
        product_data.name, product_data.price, product_data.description, product_data.image_url
    )
    
    await conn.close()
    
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
async def list_products():
    conn = await get_db()
    products = await conn.fetch("SELECT * FROM products ORDER BY created_at DESC")
    await conn.close()
    
    return {
        "products": [
            {
                "id": p['id'],
                "name": p['name'],
                "price": float(p['price']),
                "description": p['description'],
                "image_url": p['image_url'],
                "created_at": p['created_at'].isoformat()
            } for p in products
        ]
    }

@app.post("/api/virtual-tryon")
async def virtual_tryon(request: VirtualTryOnRequest, user_email: str = Depends(verify_token)):
    try:
        conn = await get_db()
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", user_email)
        user_id = user['id'] if user else None
        
        result = await process_virtual_tryon(
            request.person_image, 
            request.garment_image, 
            request.model
        )
        
        await conn.execute("""
            INSERT INTO virtual_tryons (user_id, garment_image_url, result_image_url, model_used, processing_time)
            VALUES ($1, $2, $3, $4, $5)
        """, 
            user_id,
            request.garment_image,
            result['output_image_url'],
            request.model,
            float(result['processing_time'].replace('s', ''))
        )
        
        await conn.close()
        
        return {
            "success": True,
            "output_image": result['output_image_url'],
            "model_used": request.model,
            "processing_time": result['processing_time'],
            "user": user_email
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@app.post("/api/payments/create-preference")
async def create_preference(payment_data: PaymentRequest):
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