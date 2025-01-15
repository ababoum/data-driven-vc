import asyncio
import os

import httpx


class PredictleadsClient:
    base_url = 'https://predictleads.com/api/v3'

    def __init__(self, api_token: str = None, api_key: str = None):
        self.auth_params = {
            'api_token': api_token or os.getenv('PREDICTLEADS_API_TOKEN'),
            'api_key': api_key or os.getenv('PREDICTLEADS_API_KEY')
        }

    async def fetch_github(self, website_domain: str) -> str | None:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url=f'{self.base_url}/companies/{website_domain}/github_repositories',
                params=self.auth_params
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
