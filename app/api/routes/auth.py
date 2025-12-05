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
from app.core.security import verify_password, create_access_token, get_password_hash
from app.crud.crud import get_user_by_email
from app.schemas.schemas import Token, User, UserCreate, LoginRequest

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def authenticate_user(db: Session, email: str, password: str):
    try:
        user = get_user_by_email(db, email)
        if not user or not verify_password(password, user.hashed_password):
            return False
        return user
    except Exception as e:
        print(f"Erro na autenticação: {e}")
        return False

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
        # Compatibilidade: se não tem coluna role ou erro, verifica se é o primeiro usuário
        try:
            user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
            if user_count <= 1:  # Se é o primeiro usuário, permite acesso admin
                return current_user
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado. Configure o banco primeiro em /api/auth/setup-database"
        )

# ============================================================================
# ENDPOINTS PRINCIPAIS
# ============================================================================

@router.post("/login", response_model=Token)
def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login com email e senha em JSON"""
    try:
        user = authenticate_user(db, login_data.email, login_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou senha incorretos",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no login: {str(e)}"
        )



@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Retorna dados do usuário logado"""
    return current_user

@router.post("/register")
def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra novo usuário"""
    try:
        # Verifica se email existe
        existing = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": user_data.email})
        if existing.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email já cadastrado"
            )
        
        # Cria usuário
        hashed_pw = get_password_hash(user_data.password)
        
        # Verifica se coluna role existe
        role_exists = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """)).fetchone()
        
        if role_exists:
            # Usa INSERT com role
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
                VALUES (:email, :name, :password, 'user', true, NOW())
            """), {
                "email": user_data.email,
                "name": user_data.name, 
                "password": hashed_pw
            })
        else:
            # Usa INSERT sem role
            db.execute(text("""
                INSERT INTO users (email, name, hashed_password, is_active, created_at)
                VALUES (:email, :name, :password, true, NOW())
            """), {
                "email": user_data.email,
                "name": user_data.name, 
                "password": hashed_pw
            })
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Usuário criado: {user_data.email}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )

# ============================================================================
# GOOGLE OAUTH
# ============================================================================

@router.post("/google-login")
def google_login(google_token: str, db: Session = Depends(get_db)):
    """Login/Cadastro com Google"""
    try:
        from google.auth.transport import requests as google_requests
        from google.oauth2 import id_token
        
        # Valida token do Google
        try:
            idinfo = id_token.verify_oauth2_token(
                google_token, 
                google_requests.Request(),
                os.getenv("GOOGLE_CLIENT_ID")
            )
            email = idinfo['email']
            name = idinfo['name']
        except ValueError:
            return {"error": "Token do Google inválido"}
        
        # Verifica se coluna role existe
        role_exists = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """)).fetchone()
        
        if role_exists:
            # Verifica se usuário existe com role
            existing = db.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), {"email": email})
            user_data = existing.fetchone()
            
            if user_data:
                user_id, user_email, user_name, user_role = user_data
            else:
                # Cria novo usuário com role
                db.execute(text("""
                    INSERT INTO users (email, name, hashed_password, role, is_active, created_at)
                    VALUES (:email, :name, 'google_auth', 'user', true, NOW())
                """), {"email": email, "name": name})
                db.commit()
                
                new_user = db.execute(text("SELECT id, email, name, role FROM users WHERE email = :email"), {"email": email})
                user_id, user_email, user_name, user_role = new_user.fetchone()
        else:
            # Verifica se usuário existe sem role
            existing = db.execute(text("SELECT id, email, name FROM users WHERE email = :email"), {"email": email})
            user_data = existing.fetchone()
            
            if user_data:
                user_id, user_email, user_name = user_data
                user_role = "user"
            else:
                # Cria novo usuário sem role
                db.execute(text("""
                    INSERT INTO users (email, name, hashed_password, is_active, created_at)
                    VALUES (:email, :name, 'google_auth', true, NOW())
                """), {"email": email, "name": name})
                db.commit()
                
                new_user = db.execute(text("SELECT id, email, name FROM users WHERE email = :email"), {"email": email})
                user_id, user_email, user_name = new_user.fetchone()
                user_role = "user"
        
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
    """Configuração do Google OAuth"""
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID", ""),
        "redirect_uri": os.getenv("GOOGLE_REDIRECT_URI", "")
    }

# ============================================================================
# SETUP E ADMIN
# ============================================================================

@router.get("/test-db")
def test_database(db: Session = Depends(get_db)):
    """Testa conexão com banco e estrutura"""
    try:
        # Testa conexão
        user_count = db.execute(text("SELECT COUNT(*) FROM users")).scalar()
        
        # Verifica se coluna role existe
        role_exists = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """)).fetchone()
        
        return {
            "database_connected": True,
            "users_count": user_count,
            "role_column_exists": bool(role_exists),
            "message": "Banco funcionando!" if role_exists else "Execute /setup-database para configurar"
        }
        
    except Exception as e:
        return {
            "database_connected": False,
            "error": str(e),
            "message": "Erro na conexão com banco"
        }

@router.post("/setup-database")
def setup_database(db: Session = Depends(get_db)):
    """Configura banco adicionando coluna role"""
    try:
        # Verifica se coluna existe
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """))
        
        if result.fetchone():
            # Garante que todos os usuários tenham role definido
            db.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
            db.commit()
            return {"message": "Banco já configurado e atualizado!"}
        
        # Adiciona coluna role
        db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
        db.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
        db.commit()
        
        return {
            "success": True,
            "message": "Banco configurado com sucesso! Coluna 'role' adicionada."
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao configurar banco: {str(e)}"}

@router.post("/create-admin")
def create_admin(email: str, name: str, password: str, db: Session = Depends(get_db)):
    """Cria admin (máximo 2)"""
    try:
        # Configura banco se necessário
        result = db.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role'
        """))
        
        if not result.fetchone():
            db.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'user'"))
            db.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''"))
            db.commit()
        
        # Verifica limite de admins
        try:
            admin_count = db.execute(text("SELECT COUNT(*) FROM users WHERE role = 'admin'")).scalar()
        except:
            admin_count = 0
            
        if admin_count >= 2:
            return {"error": "Máximo de 2 admins permitidos"}
        
        # Verifica se email existe
        existing = db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": email})
        if existing.fetchone():
            return {"error": "Email já cadastrado"}
        
        # Cria admin
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
        
        return {
            "success": True,
            "message": f"Admin {admin_count + 1}/2 criado: {email}"
        }
        
    except Exception as e:
        db.rollback()
        return {"error": f"Erro ao criar admin: {str(e)}"}