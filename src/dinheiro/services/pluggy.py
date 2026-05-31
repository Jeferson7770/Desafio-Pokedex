import requests
from decouple import config
from django.utils import timezone

class PluggyService:
    def __init__(self):
        self.client_id = config("PLUGGY_CLIENT_ID")
        self.client_secret = config("PLUGGY_CLIENT_SECRET")
        self.base_url = config("PLUGGY_API_URL", default="https://api.pluggy.ai")

    def _get_api_token(self):
        """Gera o token de autenticação da própria API da Pluggy"""
        url = f"{self.base_url}/auth"
        payload = {
            "clientId": self.client_id,
            "clientSecret": self.client_secret
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        return response.json()["apiKey"]

    def gerar_connect_token(self):
        """Gera o token de curta duração para o Widget abrir no Frontend"""
        api_token = self._get_api_token()
        url = f"{self.base_url}/connect_token"
        
        headers = {"X-API-KEY": api_token}
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["accessToken"]

    def buscar_contas_do_item(self, item_id):
        """Busca os saldos e dados bancários após a conexão feita no front"""
        api_token = self._get_api_token()
        url = f"{self.base_url}/accounts?itemId={item_id}"
        
        headers = {"X-API-KEY": api_token}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()["results"]