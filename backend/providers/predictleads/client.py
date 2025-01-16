import asyncio
import os

import httpx


class PredictleadsClient:
    base_url = 'https://predictleads.com/api/v3'

    def __init__(self, api_token: str = None, api_key: str = None):
        self.headers = {
            'X-Api-Key': api_token or os.getenv('PREDICTLEADS_API_KEY'),
            'X-Api-Token': api_key or os.getenv('PREDICTLEADS_API_TOKEN')
        }
        print(self.headers)

    async def fetch_company(self, website_domain: str) -> dict:
        url = f"https://predictleads.com/api/v3/companies/{website_domain}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def fetch_technologies(self, website_domain: str) -> dict:
        url = f"https://predictleads.com/api/v3/companies/{website_domain}/technology_detections?limit=50"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def fetch_tech_name(self, tech_id: str) -> dict:
        url = f"https://predictleads.com/api/v3/technologies/{tech_id}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()

    async def fetch_github(self, website_domain: str) -> str | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f'{self.base_url}/companies/{website_domain}/github_repositories',
                headers=self.headers
            )
            response.raise_for_status()
            data = response.json()
            if len(data['data']) == 0:
                return None
            url = data['data'][0]['attributes']['url']
            fullname = '/'.join(url.split('/')[-2:])
            return fullname


async def main():
    client = PredictleadsClient()
    response = await client.fetch_github('twenty.com')
    print(response)


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
