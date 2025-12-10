from fastapi import APIRouter
from app.services.viacep import ViaCEPService
from app.utils import success_response, error_response

router = APIRouter(tags=["CEP"])

@router.get("/cep/{cep}")
def consultar_cep(cep: str):
    address = ViaCEPService.get_address(cep)
    
    if not address:
        return error_response("CEP não encontrado", 404)
    
    return success_response(data=address, message="CEP encontrado")