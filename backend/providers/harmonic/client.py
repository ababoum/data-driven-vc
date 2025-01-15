import os

import requests


class HarmonicClient:
    base_url: str = "https://api.harmonic.ai"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HARMONIC_API_KEY")
        print(f"API Key: {self.api_key}")
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    @staticmethod
    def _handle_response(response: requests.Response):
        if 200 <= response.status_code < 300:
            return response.json()
        else:
            response.raise_for_status()

    def fetch_company(self, website_domain: str):
        url = f"{self.base_url}/companies"
        params = {"website_domain": website_domain}
        response = requests.post(url, headers=self.headers, params=params)
        print(response.text)
        return self._handle_response(response)
