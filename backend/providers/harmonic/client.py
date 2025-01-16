import os
import requests
from typing import List, Dict, Any, Optional

import httpx
from sklearn.ensemble import IsolationForest
import numpy as np

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
        
    async def get_company_from_urn(self, urn: str):
        url = f"{self.base_url}/companies/{urn}"
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
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

    async def get_competitors(self, website_domain: str) -> List[str]:
        """
        Get a list of similar companies (competitors) for a given domain.
        
        Args:
            website_domain (str): The domain name of the company (e.g., 'example.com')
            
        Returns:
            List[str]: A list of URNs for similar companies
            
        Raises:
            httpx.HTTPError: If the API request fails
        """
        # First get the company URN using find_company
        company_data = await self.find_company(website_domain)
        if not company_data:
            return []
            
        company_urn = company_data.get('entity_urn')
        if not company_urn:
            return []

        # Use the URN to get similar companies
        endpoint = f"{self.base_url}/search/similar_companies/{company_urn}"
        
        async with httpx.AsyncClient() as client:
            response = await client.get(endpoint, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            urns = data.get("results", [])
            
            companies = []
            for urn in urns:
                company = await self.get_company_from_urn(urn)
                companies.append(company)
            return companies
        
    def format_companies_to_md(self, companies: List[dict]) -> str:
        """
        Format a list of company data into a markdown string.
        
        Args:
            companies (List[dict]): List of company data dictionaries
            
        Returns:
            str: Formatted markdown string
        """
        if not companies:
            return "No companies found."
            
        md_output = ""
        
        for company in companies:
            md_output += f"## {company.get('name', 'Unknown Company')}\n\n"
            
            # Basic info
            if company.get('description'):
                md_output += f"**Description:** {company['description']}\n\n"
                
            if company.get('stage'):
                md_output += f"**Stage:** {company['stage']}\n"
                
            if company.get('customer_type'):
                md_output += f"**Customer Type:** {company['customer_type']}\n"
                
            if company.get('headcount'):
                md_output += f"**Headcount:** {company['headcount']}\n"
            
            md_output += "\n---\n\n"
            
        return md_output
    
    def find_outliers(self, myself: dict, others: List[dict], contamination: float = 0.3) -> List[dict]:
        """
        Find outliers in a list of companies using Isolation Forest.
        
        Args:
            myself (dict): The main company data
            others (List[dict]): List of other company data to compare against
            
        Returns:
            List[dict]: List of companies identified as outliers
        """

        # Combine myself with others into one list
        all_companies = [myself] + others
        
        # Extract numeric features for comparison
        features = []
        for company in all_companies:
            company_features = []
            # Use headcount if available
            headcount = company.get('headcount', 0)
            company_features.append(float(headcount))
            
            # Add other numeric features here as needed
            # Example: funding amount, revenue, etc.
            
            features.append(company_features)
            
        features = np.array(features)
        
        # Skip if not enough data points
        if len(features) < 2:
            return []
            
        # Fit isolation forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        iso_forest.fit(features)
        outliers = iso_forest.predict(features)
        
        # Return companies marked as outliers (-1)
        outlier_companies = []
        for idx, is_outlier in enumerate(outliers):
            if is_outlier == -1:
                outlier_companies.append(all_companies[idx])
                
        return outlier_companies