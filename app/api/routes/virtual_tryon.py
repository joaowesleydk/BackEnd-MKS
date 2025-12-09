import requests
import time
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class VirtualTryOnRequest(BaseModel):
    person_image: str
    cloth_image: str

@router.post("/virtual-tryon")
async def virtual_tryon(request: VirtualTryOnRequest):
    """Endpoint para provador virtual usando Replicate API"""
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        raise HTTPException(status_code=500, detail="Token do Replicate não configurado")
    
    try:
        response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {replicate_token}",
                "Content-Type": "application/json"
            },
            json={
                "version": "c871bb9b046607b680449ecbae55fd8c6d945e0a1948644bf2361b3d021d3ff4",
                "input": {
                    "human_img": request.person_image,
                    "garm_img": request.cloth_image,
                    "garment_des": "clothing item"
                }
            }
        )
        
        if response.status_code != 201:
            raise HTTPException(status_code=500, detail="Erro ao iniciar processamento")
        
        prediction_id = response.json()["id"]
        
        # Aguarda processamento (máximo 60 segundos)
        for _ in range(60):
            time.sleep(1)
            result = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {replicate_token}"}
            ).json()
            
            if result["status"] == "succeeded":
                return {"result_image": result["output"]}
            elif result["status"] == "failed":
                raise HTTPException(status_code=500, detail="Processamento falhou")
        
        raise HTTPException(status_code=408, detail="Timeout no processamento")
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Erro na API: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")