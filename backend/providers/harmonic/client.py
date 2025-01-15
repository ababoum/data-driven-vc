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

    async def find_company(self, website_domain: str):
        url = f"{self.base_url}/companies"
        params = {"website_domain": website_domain}
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()

    async def fetch_person(self, person_id: str):
        url = f"{self.base_url}/persons/{person_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def find_employees_experience(self, website_domain: str) -> list[dict]:
        company_data = await self.find_company(website_domain)
        if not company_data:
            return []

        person_ids = [p['person'] for p in company_data['people']]
        people_data = []
        for person_id in person_ids:
            person_data = await self.fetch_person(person_id)
            people_data.append(person_data)
        return people_data
