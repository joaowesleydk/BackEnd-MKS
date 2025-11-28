# Instalar: pip install cloudinary
import cloudinary
import cloudinary.uploader
from fastapi import UploadFile
import os

# Configuração (adicione no .env)
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

async def upload_to_cloudinary(file: UploadFile):
    """Upload de imagem para Cloudinary"""
    try:
        # Lê o arquivo
        contents = await file.read()
        
        # Faz upload
        result = cloudinary.uploader.upload(
            contents,
            folder="mks-store",  # Organiza em pasta
            resource_type="image"
        )
        
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        raise Exception(f"Erro no upload: {str(e)}")

# Exemplo de uso no endpoint
@router.post("/upload-cloudinary")
async def upload_image_cloudinary(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    result = await upload_to_cloudinary(file)
    return result