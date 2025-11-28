# Instalar: pip install boto3
import boto3
from fastapi import UploadFile
import os
from uuid import uuid4

# Configuração S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION", "us-east-1")
)

BUCKET_NAME = os.getenv("S3_BUCKET_NAME")

async def upload_to_s3(file: UploadFile):
    """Upload de imagem para S3"""
    try:
        # Gera nome único
        file_extension = file.filename.split(".")[-1]
        file_name = f"products/{uuid4()}.{file_extension}"
        
        # Lê o arquivo
        contents = await file.read()
        
        # Faz upload
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=contents,
            ContentType=file.content_type,
            ACL='public-read'  # Torna público
        )
        
        # URL pública
        url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{file_name}"
        
        return {"url": url, "key": file_name}
        
    except Exception as e:
        raise Exception(f"Erro no upload S3: {str(e)}")

@router.post("/upload-s3")
async def upload_image_s3(
    file: UploadFile = File(...),
    admin_user: User = Depends(get_admin_user)
):
    result = await upload_to_s3(file)
    return result