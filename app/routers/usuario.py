from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User
from app.auth import get_current_user
from app.utils import success_response, error_response
import base64
from PIL import Image
import io

router = APIRouter(prefix="/usuario", tags=["Usuario"])

class UserProfile(BaseModel):
    nome: str = None
    bio: str = None
    tema_cor: str = None
    foto: str = None

@router.get("/perfil")
def get_perfil(current_user: User = Depends(get_current_user)):
    return success_response(data={
        "id": current_user.id,
        "email": current_user.email,
        "nome": current_user.nome,
        "foto": current_user.foto,
        "bio": current_user.bio,
        "tema_cor": current_user.tema_cor,
        "role": current_user.role
    }, message="Perfil carregado")

@router.put("/perfil")
def update_perfil(profile_data: UserProfile, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if profile_data.nome:
        current_user.nome = profile_data.nome
    if profile_data.bio:
        current_user.bio = profile_data.bio
    if profile_data.tema_cor:
        current_user.tema_cor = profile_data.tema_cor
    if profile_data.foto:
        current_user.foto = profile_data.foto
    
    db.commit()
    return success_response(message="Perfil atualizado com sucesso")

@router.post("/upload-foto")
async def upload_foto(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        return error_response("Arquivo deve ser uma imagem", 400)
    
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        # Redimensionar se necessário
        if image.width > 500 or image.height > 500:
            image.thumbnail((500, 500), Image.Resampling.LANCZOS)
        
        # Converter para base64
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        image_base64 = f"data:image/jpeg;base64,{base64.b64encode(buffer.getvalue()).decode()}"
        
        # Salvar no perfil
        current_user.foto = image_base64
        db.commit()
        
        return success_response(data={"foto": image_base64}, message="Foto atualizada com sucesso")
    
    except Exception as e:
        return error_response(f"Erro ao processar imagem: {str(e)}", 400)