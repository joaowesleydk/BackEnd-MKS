#!/usr/bin/env python3
"""
Teste do sistema de login simplificado
Apenas email e senha em formato JSON
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_register():
    """Testa registro de usuário"""
    url = f"{BASE_URL}/api/auth/register"
    data = {
        "email": "teste@exemplo.com",
        "name": "Usuário Teste",
        "password": "123456"
    }
    
    response = requests.post(url, json=data)
    print("=== REGISTRO ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_login():
    """Testa login de usuário"""
    url = f"{BASE_URL}/api/auth/login"
    data = {
        "email": "teste@exemplo.com",
        "password": "123456"
    }
    
    response = requests.post(url, json=data)
    print("=== LOGIN ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return token
    return None

def test_me(token):
    """Testa endpoint /me com token"""
    url = f"{BASE_URL}/api/auth/me"
    headers = {"Authorization": f"Bearer {token}"}
    
    response = requests.get(url, headers=headers)
    print("=== DADOS DO USUÁRIO ===")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

if __name__ == "__main__":
    print("Testando sistema de login simplificado...")
    print()
    
    # Registra usuário
    test_register()
    
    # Faz login
    token = test_login()
    print()
    
    # Testa dados do usuário
    if token:
        test_me(token)