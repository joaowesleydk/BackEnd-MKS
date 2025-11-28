#!/usr/bin/env python3
"""
Script para tornar um usuário admin
Uso: python make_admin.py email@exemplo.com
"""
import sys
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, engine
from app.models.models import User

def make_user_admin(email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"❌ Usuário com email '{email}' não encontrado!")
            return False
        
        if user.role == "admin":
            print(f"✅ Usuário '{email}' já é admin!")
            return True
            
        user.role = "admin"
        db.commit()
        print(f"✅ Usuário '{email}' agora é admin!")
        return True
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python make_admin.py email@exemplo.com")
        sys.exit(1)
    
    email = sys.argv[1]
    make_user_admin(email)