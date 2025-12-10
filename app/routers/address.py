from fastapi import APIRouter, HTTPException
from app.services.viacep import ViaCEPService

router = APIRouter(prefix="/address", tags=["Address"])

@router.get("/cep/{cep}")
def get_address_by_cep(cep: str):
    """Consultar endereço pelo CEP usando ViaCEP"""
    
    address = ViaCEPService.get_address(cep)
    
    if not address:
        raise HTTPException(status_code=404, detail="CEP not found")
    
    return address