from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from jwt.exceptions import InvalidTokenError
from app.core.database import get_db
from app.core.config import settings
from app.core.security import verify_password, create_access_token
from app.crud.crud import get_user_by_email
from app.schemas.schemas import Token, User, UserCreate

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_admin_user(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Admin privileges required."
        )
    return current_user

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/simple-register")
def simple_register(email: str, name: str, password: str, db: Session = Depends(get_db)):
    """Registro simples de usuário"""
    try:
        from app.crud.crud import create_user, get_user_by_email
        from app.schemas.schemas import UserCreate
        
        # Verifica se já existe
        if get_user_by_email(db, email):
            return {"error": "Email já cadastrado"}
        
        # Cria usuário
        user_data = UserCreate(email=email, name=name, password=password)
        new_user = create_user(db, user_data)
        
        return {
            "success": True,
            "message": f"Usuário criado: {email}",
            "user_id": new_user.id
        }
        
    except Exception as e:
        return {"error": f"Erro: {str(e)}"}

@router.post("/create-admin")
def create_admin(
    email: str,
    name: str, 
    password: str,
    db: Session = Depends(get_db)
):
    """Cria admin (máximo 2 permitidos)"""
    try:
        from app.models.models import User as UserModel
        from app.core.security import get_password_hash
        
        # Conta admins existentes
        admin_count = db.query(UserModel).filter(UserModel.role == "admin").count()
        if admin_count >= 2:
            return {"error": "Máximo de 2 admins permitidos"}
        
        # Verifica se email existe
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            return {"error": "Email já cadastrado"}
        
        # Cria admin
        hashed_pw = get_password_hash(password)
        new_admin = UserModel(
            email=email,
            name=name,
            hashed_password=hashed_pw,
            role="admin"
        )
        
        db.add(new_admin)
        db.commit()
        
        return {
            "success": True,
            "message": f"Admin criado: {email}",
            "admin_number": admin_count + 1
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro interno: {str(e)}"}