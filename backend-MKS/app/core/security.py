# app/core/security.py
# --------------------
# Funções para hash de senha (bcrypt) e criação/validação de JWT
import bcrypt
from datetime import datetime, timedelta
import jwt  # PyJWT
from app.core.config import settings

# Hash de senha com bcrypt
def hash_password(plain_password: str) -> str:
    # bcrypt exige bytes
    hashed = bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt())
    return hashed.decode()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())

# Cria token JWT simples
def create_access_token(data: dict, expires_minutes: int | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=(expires_minutes or settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt

def decode_token(token: str) -> dict:
    # Pode lançar exceções se inválido/expirado
    return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
