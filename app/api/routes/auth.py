from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
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
    # Verifica se o usuário tem role de admin
    if hasattr(current_user, 'role') and current_user.role == "admin":
        return current_user
    
    # Se não tem o campo role, permite (compatibilidade)
    if not hasattr(current_user, 'role'):
        return current_user
        
    # Se tem role mas não é admin, bloqueia
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Acesso negado. Apenas admins podem realizar esta ação."
    )

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

@router.post("/setup-database")
def setup_database(db: Session = Depends(get_db)):
    """Configura o banco de dados adicionando coluna role"""
    try:
        from sqlalchemy import text
        
        # Verifica se a coluna já existe
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """))
        
        if result.fetchone():
            return {"message": "Banco já configurado! Coluna 'role' existe."}
        
        # Adiciona a coluna role
        db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
        
        # Atualiza usuários existentes
        db.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
        
        db.commit()
        
        return {
            "success": True,
            "message": "Banco configurado! Coluna 'role' adicionada.",
            "note": "Agora você pode criar admins"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro na configuração: {str(e)}"}

@router.post("/create-first-admin")
def create_first_admin(
    email: str,
    name: str, 
    password: str,
    db: Session = Depends(get_db)
):
    """Cria o primeiro admin (apenas se não existir nenhum)"""
    try:
        from app.models.models import User as UserModel
        from app.core.security import get_password_hash
        
        # Verifica se já existe admin
        admin_count = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        if admin_count > 0:
            return {"error": "Já existe um admin no sistema"}
        
        # Verifica se email existe
        existing = db.query(UserModel).filter(UserModel.email == email).first()
        if existing:
            return {"error": "Email já cadastrado"}
        
        # Cria primeiro admin
        hashed_pw = get_password_hash(password)
        
        # Insere diretamente com SQL para garantir que funcione
        db.execute(text("""
            INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
            VALUES (:email, :name, :password, 'admin', true, NOW())
        """), {
            "email": email,
            "name": name, 
            "password": hashed_pw
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Primeiro admin criado: {email}",
            "note": "Agora faça login para gerenciar produtos"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro: {str(e)}"}