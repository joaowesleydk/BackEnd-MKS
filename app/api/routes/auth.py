from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import text
import jwt
from jwt.exceptions import InvalidTokenError
import os
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

def get_admin_user(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        # Verifica role diretamente no banco
        result = db.execute(text("SELECT role FROM users WHERE id = :user_id"), {"user_id": current_user.id})
        user_role = result.scalar()
        
        if user_role == "admin":
            return current_user
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Acesso negado. Apenas admins podem realizar esta ação."
            )
    except Exception:
        # Se der erro (coluna não existe), permite acesso (compatibilidade)
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

@router.post("/register-user")
def register_user(email: str, name: str, password: str, db: Session = Depends(get_db)):
    """Registra usuário normal"""
    try:
        from app.core.security import get_password_hash
        
        # Verifica se email existe
        existing = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        if existing.fetchone():
            return {"error": "Email já cadastrado"}
        
        # Cria usuário normal
        hashed_pw = get_password_hash(password)
        
        db.execute(text("""
            INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
            VALUES (:email, :name, :password, 'user', true, NOW())
        """), {
            "email": email,
            "name": name, 
            "password": hashed_pw
        })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Usuário criado: {email}",
            "role": "user"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro: {str(e)}"}

@router.post("/google-login")
def google_login(google_token: str, db: Session = Depends(get_db)):
    """Login/Cadastro com Google"""
    try:
        import requests
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        
        # Verifica token do Google
        try:
            # Valida o token com Google
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                google_requests.Request(),
                os.getenv("GOOGLE_CLIENT_ID")
            )
            
            email = idinfo['email']
            name = idinfo['name']
            
        except ValueError:
            return {"error": "Token do Google inválido"}
        
        # Verifica se usuário já existe
        existing = db.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), {"email": email})
        user_data = existing.fetchone()
        
        if user_data:
            # Usuário existe - faz login
            user_id, user_email, user_name, user_role = user_data
        else:
            # Usuário não existe - cria conta
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
                VALUES (:email, :name, 'google_auth', 'user', true, NOW())
            """), {
                "email": email,
                "name": name
            })
            db.commit()
            
            # Busca o usuário recém criado
            new_user = db.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), {"email": email})
            user_id, user_email, user_name, user_role = new_user.fetchone()
        
        # Cria token JWT
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": email}, expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "email": user_email,
                "name": user_name,
                "role": user_role
            }
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro no login Google: {str(e)}"}

@router.get("/google-config")
def get_google_config():
    """Retorna configuração do Google OAuth para o frontend"""
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", "sua-google-client-id"),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:3000")
    }

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

@router.post("/create-admin-complete")
def create_admin_complete(
    email: str,
    name: str, 
    password: str,
    db: Session = Depends(get_db)
):
    """Configura banco E cria admin em uma só operação"""
    try:
        from app.core.security import get_password_hash
        
        # PASSO 1: Verifica/Cria coluna role
        try:
            # Tenta verificar se coluna existe
            result = db.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            """))
            
            if not result.fetchone():
                # Adiciona coluna se não existir
                db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
                db.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
                db.commit()
        except Exception as setup_error:
            return {"error": f"Erro na configuração do banco: {str(setup_error)}"}
        
        # PASSO 2: Verifica se email já existe
        existing_check = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        if existing_check.fetchone():
            return {"error": "Email já cadastrado"}
        
        # PASSO 3: Verifica quantos admins existem
        admin_count = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        if admin_count >= 2:
            return {"error": "Máximo de 2 admins permitidos"}
        
        # PASSO 4: Cria admin
        hashed_pw = get_password_hash(password)
        
        db.execute(text("""
            INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
            VALUES (:email, :name, :password, 'admin', true, NOW())
        """), {
            "email": email,
            "name": name, 
            "password": hashed_pw
        })
        
        db.commit()
        
        admin_number = admin_count + 1
        return {
            "success": True,
            "message": f"Admin {admin_number}/2 criado: {email}",
            "note": "Banco configurado e admin criado! Faça login agora."
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro: {str(e)}"}