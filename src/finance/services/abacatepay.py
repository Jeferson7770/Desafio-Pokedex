import requests
from decouple import config
from rest_framework.exceptions import ValidationError

class AbacatePayService:
    def __init__(self):
        self.api_key = config("ABACATEPAY_API_KEY")
        self.base_url = "https://api.abacatepay.com/v2"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def criar_checkout_assinatura(self, produto_id, external_id, metadata=None):
        url = f"{self.base_url}/subscriptions/create"

        frontend_url = config("FRONTEND_URL", default="").rstrip("/")
        if frontend_url:
            completion_url = f"{frontend_url}/app/payment/success"
            return_url = f"{frontend_url}/app/payment/return"
        else:
            completion_url = config("ABACATEPAY_COMPLETION_URL")
            return_url = config("ABACATEPAY_RETURN_URL")

        payload = {
            "items": [
                {
                    "id": produto_id,
                    "quantity": 1
                }
            ],
            "externalId": str(external_id),
            "completionUrl": completion_url,
            "returnUrl": return_url,
            "methods": ["CARD"]
        }

        if metadata:
            payload["metadata"] = metadata

        try:
            response = requests.post(url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                return response.json()
                
            raise ValidationError({
                "detail": f"Erro retornado pela AbacatePay ({response.status_code}): {response.text}"
            })
        except requests.RequestException as e:
            raise ValidationError({"detail": f"Falha catastrófica de comunicação com gateway: {str(e)}"})

    def listar_produtos(self, limit=100, status_filter="ACTIVE"):
        url = f"{self.base_url}/products/list"
        params = {"limit": limit}

        try:
            response = requests.get(url, headers=self.headers, params=params)

            if response.status_code == 200:
                data = response.json()
                produtos = data.get("data", [])
                if status_filter:
                    produtos = [p for p in produtos if p.get("status") == status_filter]
                return produtos

            raise ValidationError({
                "detail": f"Erro retornado pela AbacatePay ({response.status_code}): {response.text}"
            })
        except requests.RequestException as e:
            raise ValidationError({"detail": f"Falha de comunicação com gateway ao listar produtos: {str(e)}"})