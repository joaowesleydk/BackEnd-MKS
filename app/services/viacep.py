import requests
from typing import Dict, Optional

class ViaCEPService:
    @staticmethod
    def get_address(cep: str) -> Optional[Dict[str, str]]:
        cep = cep.replace("-", "").replace(".", "")
        
        if len(cep) != 8:
            return None
        
        try:
            response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
            if response.status_code == 200:
                data = response.json()
                if "erro" not in data:
                    return {
                        "cep": data["cep"],
                        "logradouro": data["logradouro"],
                        "bairro": data["bairro"],
                        "cidade": data["localidade"],
                        "uf": data["uf"]
                    }
            return None
        except:
            return None
    
    @staticmethod
    def calculate_shipping(cep: str, total: float) -> Dict[str, float]:
        # Frete grátis acima de R$ 150
        if total >= 150.0:
            return {"frete": 0.0, "prazo": 5}
        
        # Simulação simples de frete por região
        address = ViaCEPService.get_address(cep)
        if not address:
            return {"frete": 15.0, "prazo": 10}
        
        # Frete por estado (simulação)
        frete_por_estado = {
            "SP": 10.0, "RJ": 12.0, "MG": 15.0, "RS": 18.0,
            "PR": 16.0, "SC": 17.0, "GO": 20.0, "DF": 18.0,
            "BA": 22.0, "PE": 25.0, "CE": 28.0, "AM": 35.0
        }
        
        uf = address["uf"]
        frete = frete_por_estado.get(uf, 20.0)
        prazo = 7 if uf in ["SP", "RJ", "MG"] else 10
        
        return {"frete": frete, "prazo": prazo}