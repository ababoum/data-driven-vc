import os

import httpx


class HarmonicClient:
    base_url: str = "https://api.harmonic.ai"

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HARMONIC_API_KEY")
        self.headers = {
            "apikey": self.api_key,
            "Content-Type": "application/json"
        }

    async def fetch_company(self, website_domain: str):
        url = f"{self.base_url}/companies"
        params = {"website_domain": website_domain}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
