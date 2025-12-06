#!/usr/bin/env python3
"""
Exemplo de como testar o upload de imagens de produtos
"""

import requests
import os

# Configurações
API_BASE = "https://backend-mks-1.onrender.com"  # ou "http://localhost:8000"
LOGIN_URL = f"{API_BASE}/api/auth/login"
UPLOAD_URL = f"{API_BASE}/api/products/frontend-create-with-file"

def test_upload_product():
    """Testa o upload de produto com imagem"""
    
    # 1. Fazer login para obter token
    login_data = {
        "email": "joaodkind@gmail.com",
        "password": "@Jacutinga011"
    }
    
    print("1. Fazendo login...")
    login_response = requests.post(LOGIN_URL, json=login_data)
    
    if login_response.status_code != 200:
        print(f"Erro no login: {login_response.text}")
        return
    
    token = login_response.json()["access_token"]
    print("✅ Login realizado com sucesso!")
    
    # 2. Preparar dados do produto
    product_data = {
        "name": "Vestido Floral Verão",
        "price": 89.90,
        "category": "Vestidos",
        "description": "Lindo vestido floral perfeito para o verão",
        "promocao": False
    }
    
    # 3. Preparar arquivo de imagem (exemplo)
    # Você pode usar qualquer imagem JPG, PNG, GIF ou WebP
    image_path = "exemplo_produto.jpg"  # Substitua pelo caminho da sua imagem
    
    if not os.path.exists(image_path):
        print(f"❌ Arquivo de imagem não encontrado: {image_path}")
        print("Crie um arquivo de imagem ou altere o caminho em image_path")
        return
    
    # 4. Fazer upload
    print("2. Fazendo upload do produto...")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    with open(image_path, "rb") as image_file:
        files = {"imagemFile": image_file}
        
        response = requests.post(
            UPLOAD_URL,
            headers=headers,
            data=product_data,
            files=files
        )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Produto criado com sucesso!")
        print(f"📦 Produto: {result['produto']['name']}")
        print(f"💰 Preço: R$ {result['produto']['price']}")
        print(f"🖼️ Imagem: {result['produto']['image']}")
    else:
        print(f"❌ Erro no upload: {response.text}")

def test_with_curl():
    """Mostra exemplo com curl"""
    print("\n" + "="*50)
    print("EXEMPLO COM CURL:")
    print("="*50)
    
    curl_example = '''
# 1. Fazer login
curl -X POST "https://backend-mks-1.onrender.com/api/auth/login" \\
  -H "Content-Type: application/json" \\
  -d '{"email": "joaodkind@gmail.com", "password": "@Jacutinga011"}'

# 2. Upload do produto (substitua SEU_TOKEN pelo token recebido)
curl -X POST "https://backend-mks-1.onrender.com/api/products/frontend-create-with-file" \\
  -H "Authorization: Bearer SEU_TOKEN" \\
  -F "name=Vestido Floral" \\
  -F "price=89.90" \\
  -F "category=Vestidos" \\
  -F "description=Lindo vestido floral" \\
  -F "promocao=false" \\
  -F "imagemFile=@caminho/para/sua/imagem.jpg"

# 3. Acessar a imagem
# A imagem ficará disponível em:
# https://backend-mks-1.onrender.com/uploads/products/NOME_DO_ARQUIVO.jpg
'''
    
    print(curl_example)

if __name__ == "__main__":
    print("🧪 TESTE DE UPLOAD DE PRODUTOS")
    print("="*40)
    
    # Descomente a linha abaixo para testar com Python
    # test_upload_product()
    
    # Mostra exemplo com curl
    test_with_curl()