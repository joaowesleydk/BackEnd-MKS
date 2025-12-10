from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from app.database import get_db
from app.models.user import User
from app.auth import verify_password, get_password_hash, create_access_token, get_current_user
from google.auth.transport import requests
from google.oauth2 import id_token
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    nome: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class GoogleLogin(BaseModel):
    token: str

class UserProfile(BaseModel):
    nome: str
    foto: str = None
    bio: str = None
    tema_cor: str = "#000000"

@router.post("/register")
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        nome=user_data.nome
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role})
    return {"success": True, "data": {"access_token": access_token, "token_type": "bearer", "user": {
        "id": user.id, "email": user.email, "nome": user.nome, "role": user.role
    }}, "message": "Usuário registrado com sucesso"}

@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role})
    return {"success": True, "data": {"access_token": access_token, "token_type": "bearer", "user": {
        "id": user.id, "email": user.email, "nome": user.nome, "role": user.role
    }}, "message": "Login realizado com sucesso"}

@router.post("/google")
def google_login(google_data: GoogleLogin, db: Session = Depends(get_db)):
    try:
        idinfo = id_token.verify_oauth2_token(
            google_data.token, requests.Request(), os.getenv("GOOGLE_CLIENT_ID")
        )
        
        email = idinfo['email']
        nome = idinfo['name']
        foto = idinfo.get('picture')
        google_id = idinfo['sub']
        
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                email=email,
                nome=nome,
                foto=foto,
                google_id=google_id
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        access_token = create_access_token(data={"sub": user.email, "user_id": user.id, "role": user.role})
        return {"success": True, "data": {"access_token": access_token, "token_type": "bearer", "user": {
            "id": user.id, "email": user.email, "nome": user.nome, "role": user.role
        }}, "message": "Login Google realizado com sucesso"}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google token")

@router.get("/me")
def get_profile(current_user: User = Depends(get_current_user)):
    return {"success": True, "data": {
        "id": current_user.id,
        "email": current_user.email,
        "nome": current_user.nome,
        "foto": current_user.foto,
        "bio": current_user.bio,
        "tema_cor": current_user.tema_cor,
        "role": current_user.role
    }, "message": "Perfil carregado"}

@router.put("/profile")
def update_profile(profile_data: UserProfile, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    current_user.nome = profile_data.nome
    current_user.foto = profile_data.foto
    current_user.bio = profile_data.bio
    current_user.tema_cor = profile_data.tema_cor
    db.commit()
    return {"success": True, "data": None, "message": "Perfil atualizado com sucesso"}