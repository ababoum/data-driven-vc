import requests

class HarmonicAPI:
    def __init__(self, base_harmonic_url: str, api_key: str):
        self.base_harmonic_url = base_harmonic_url
        self.api_key = api_key

    def get_company(self, id_or_urn: str):
        url = f'{self.base_harmonic_url}/companies/{id_or_urn}'
        response = requests.get(url, headers={"apikey": f"{self.api_key}"})

        if response.status_code != 200:
            raise Exception(f"Error: {response.text}")

        return response.json()

    def get_person(self, id_or_urn: str):
        url = f'{self.base_harmonic_url}/persons/{id_or_urn}'
        response = requests.get(url, headers={"apikey": f"{self.api_key}"})

        if response.status_code != 200:
            raise Exception(f"Error: {response.text}")

        return response.json()

    def get_competitors(self, id_or_urn: str, resolve_urn: bool = True):
        url = f'{self.base_harmonic_url}/search/similar_companies/{id_or_urn}'
        response = requests.get(url, headers={"apikey": f"{self.api_key}"})

        if response.status_code != 200:
            raise Exception(f"Error: {response.text}")

        json = response.json()
        if 'results' in json and json['results']:
            urns = json['results']

            if not resolve_urn:
                return urns

            return [self.get_company(urn) for urn in urns]
        return []


    def get_enriched_company(self, website_domain: str = None, linkedin_url: str = None):
        if not website_domain and not linkedin_url:
            raise Exception("Please provide either website_domain or linkedin_url")

        url = f'{self.base_harmonic_url}/companies'

        payload = {}
        if website_domain:
            payload["website_domain"] = website_domain
        else:
            payload["linkedin_url"] = linkedin_url

        response = requests.post(url, headers={"apikey": f"{self.api_key}"}, json={}, params=payload)
        if response.status_code != 200:
            raise Exception(f"Error: {response.text}")

        return response.json()

    def get_founders_from_company(self, company):
        if 'people' not in company:
            return []

        people = company['people']
        founder_urns = [person['person'] for person in people if 'role_type' in person and 'person' in person and person['role_type'] == 'FOUNDER']

        return [self.get_person(urn) for urn in founder_urns]