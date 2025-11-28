import os
import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.api.routes.auth import get_admin_user
from app.schemas.schemas import User

router = APIRouter()

# Configuração Cloudinary
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    # Validações de segurança
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Arquivo deve ser uma imagem")
    
    if file.size > 5_000_000:  # 5MB máximo
        raise HTTPException(status_code=400, detail="Arquivo muito grande (máximo 5MB)")
    
    allowed_extensions = ["jpg", "jpeg", "png", "webp"]
    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in allowed_extensions:
        raise HTTPException(status_code=400, detail="Formato não permitido. Use: jpg, png, webp")
    
    try:
        # Lê o arquivo
        contents = await file.read()
        
        # Upload para Cloudinary
        result = cloudinary.uploader.upload(
            contents,
            folder="mks-store/products",
            resource_type="image",
            transformation=[
                {"width": 800, "height": 800, "crop": "limit"},
                {"quality": "auto"},
                {"format": "auto"}
            ]
        )
        
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result["width"],
            "height": result["height"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no upload: {str(e)}")

@router.delete("/image/{public_id}")
async def delete_image(
    public_id: str,
    admin_user: User = Depends(get_admin_user)
):
    try:
        result = cloudinary.uploader.destroy(public_id)
        return {"message": "Imagem deletada com sucesso", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar: {str(e)}")