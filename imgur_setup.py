# Instalar: pip install requests
import requests
import base64
from fastapi import UploadFile
import os

IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")

async def upload_to_imgur(file: UploadFile):
    """Upload de imagem para Imgur"""
    try:
        # Lê e converte para base64
        contents = await file.read()
        image_b64 = base64.b64encode(contents).decode()
        
        # Headers
        headers = {
            'Authorization': f'Client-ID {IMGUR_CLIENT_ID}',
            'Content-Type': 'application/json'
        }
        
        # Dados
        data = {
            'image': image_b64,
            'type': 'base64'
        }
        
        # Faz upload
        response = requests.post(
            'https://api.imgur.com/3/image',
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "url": result["data"]["link"],
                "delete_hash": result["data"]["deletehash"]
            }
        else:
            raise Exception(f"Erro Imgur: {response.text}")
            
    except Exception as e:
        raise Exception(f"Erro no upload: {str(e)}")

@router.post("/upload-imgur")
async def upload_image_imgur(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    result = await upload_to_imgur(file)
    return result