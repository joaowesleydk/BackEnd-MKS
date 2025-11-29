#!/usr/bin/env python3
"""
Script para adicionar coluna role na tabela users
Execute: python add_role_migration.py
"""
import os
from sqlalchemy import create_engine, text
from app.core.config import settings

def add_role_column():
    """Adiciona coluna role na tabela users"""
    try:
        # Conecta ao banco
        engine = create_engine(settings.database_url)
        
        with engine.connect() as conn:
            # Verifica se a coluna já existe
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='role'
            """))
            
            if result.fetchone():
                print("✅ Coluna 'role' já existe!")
                return True
            
            # Adiciona a coluna role
            conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
            
            # Atualiza usuários existentes para 'user'
            conn.execute(text("UPDATE users SET role = 'user' WHERE role IS NULL"))
            
            # Commit das mudanças
            conn.commit()
            
            print("✅ Coluna 'role' adicionada com sucesso!")
            print("✅ Usuários existentes definidos como 'user'")
            return True
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

if __name__ == "__main__":
    add_role_column()