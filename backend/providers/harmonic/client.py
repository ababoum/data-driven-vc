import os
from typing import List

import httpx
import numpy as np
from sklearn.ensemble import IsolationForest


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
            print(self.headers)
            response = await client.post(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        
    async def get_company_from_urn(self, urn: str) -> dict:
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

    async def get_competitors(self, website_domain: str) -> List[dict]:
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
    
    def find_outliers(self, myself: dict, others: List[dict], contamination: float = 0.3) -> tuple[List[dict], dict]:
        """
        Find outliers in a list of companies using Isolation Forest and return feature importance.
        
        Args:
            myself (dict): The main company data
            others (List[dict]): List of other company data to compare against
            contamination (float): The proportion of outliers in the dataset
            
        Returns:
            tuple[List[dict], dict]: Tuple containing:
                - List of companies identified as outliers
                - Dictionary of feature importance metrics
        """
        # Combine myself with others into one list
        all_companies = [myself] + others
        
        # Define features to analyze
        feature_names = [
            'headcount',
            'funding_rounds_count',
            'total_funding',
            'last_funding',
            'stage_score'
        ]
        
        # Stage scoring mapping
        stage_scores = {
            'SEED': 1,
            'SERIES_A': 2,
            'SERIES_B': 3,
            'SERIES_C': 4,
            'SERIES_D': 5,
            'SERIES_E': 6,
            'IPO': 7,
            'ACQUIRED': 8,
            'UNKNOWN': 0
        }
        
        # Extract numeric features for comparison
        features = []
        for company in all_companies:
            company_features = []
            
            # Headcount
            headcount = float(company.get('headcount', 0))
            company_features.append(headcount)
            
            # Number of funding rounds
            funding_rounds = len(company.get('funding_rounds', []))
            company_features.append(float(funding_rounds))
            
            # Total funding amount
            total_funding = sum(
                round.get('amount', 0) 
                for round in company.get('funding_rounds', [])
            )
            company_features.append(float(total_funding))
            
            # Last funding amount (most recent round)
            last_funding = (
                company.get('funding_rounds', [])[-1].get('amount', 0)
                if company.get('funding_rounds')
                else 0
            )
            company_features.append(float(last_funding))
            
            # Stage score
            stage = company.get('stage', 'UNKNOWN')
            stage_score = stage_scores.get(stage, 0)
            company_features.append(float(stage_score))
            
            features.append(company_features)
            
        features = np.array(features)
        
        # Skip if not enough data points
        if len(features) < 2:
            return [], {}
            
        # Fit isolation forest
        iso_forest = IsolationForest(contamination=contamination, random_state=42)
        iso_forest.fit(features)
        outliers = iso_forest.predict(features)
        
        # Calculate feature importance using decision paths
        feature_importance = {}
        
        # For each feature, calculate its importance based on how often it's used in decision paths
        for idx, feature_name in enumerate(feature_names):
            # Calculate how often this feature is used in decision paths
            feature_usage = np.sum([
                1 for estimator in iso_forest.estimators_
                if idx in estimator.tree_.feature
            ])
            feature_importance[feature_name] = feature_usage / len(iso_forest.estimators_)
        
        # Normalize feature importance
        total_importance = sum(feature_importance.values())
        if total_importance > 0:
            feature_importance = {
                k: round(v / total_importance * 100, 2)
                for k, v in feature_importance.items()
            }
        
        # Return companies marked as outliers (-1) and feature importance
        outlier_companies = []
        for idx, is_outlier in enumerate(outliers):
            if is_outlier == -1:
                outlier_companies.append(all_companies[idx])
                
        return outlier_companies, feature_importance
    
    async def get_founders_from_company(self, company):
        if 'people' not in company:
            return []

        people = company['people']
        founder_urns = [person['person'] for person in people if 'role_type' in person and 'person' in person and person['role_type'] == 'FOUNDER']

        return [await self.fetch_person(urn) for urn in founder_urns]

<<<<<<< HEAD
    def format_founders_to_md(self, founders: List[dict], founders_backgrounds: List[dict]) -> str:
=======
    def format_founders_to_md(self, founders: list[dict]) -> str:
>>>>>>> 34f2ee2302537c8f5a306b43124d41706c6003ce
        """
        Format founders' information into a markdown string.
        
        Args:
            founders (List[Dict]): List of founder data dictionaries
            founders_backgrounds (List[Dict]): List of founder background analysis
            
        Returns:
            str: Formatted markdown string
        """
        if not founders:
            return "No founder information available."
            
        md_output = ""
        
        for i, founder in enumerate(founders):
            background = founders_backgrounds[i] if i < len(founders_backgrounds) else None
            
            # Basic Info
            md_output += f"## {founder.get('full_name', 'Unknown Founder')}\n\n"
            
            # Overall Assessment (if available)
            if background and background.get('global'):
                sentiment = background['global']['sentiment'].upper()
                reason = background['global']['sentiment_reason']
                md_output += f"**Overall Assessment:** {sentiment}\n"
                md_output += f"_{reason}_\n\n"
            
            # Current Role
            current_roles = [exp for exp in founder.get('experience', []) 
                           if exp.get('is_current_position') and exp.get('company_name')]
            if current_roles:
                md_output += f"**Current Role:** {current_roles[0].get('title', 'Unknown')} at {current_roles[0].get('company_name', 'Unknown Company')}\n\n"
            
            # Education with Sentiment
            if background and background.get('global_education'):
                edu_sentiment = background['global_education']['sentiment'].upper()
                edu_reason = background['global_education']['sentiment_reason']
                md_output += f"### Education ({edu_sentiment})\n"
                md_output += f"_{edu_reason}_\n\n"
            
            if background and background.get('educations'):
                sorted_education = sorted(
                    background['educations'],
                    key=lambda x: x.get('end_date') or '',
                    reverse=True
                )
                for edu in sorted_education:
                    school = edu.get('school_name', '')
                    degree = edu.get('degree', '')
                    field = edu.get('field', '')
                    sentiment = edu.get('sentiment', '').upper()
                    
                    md_output += f"- **{school}** - {degree}"
                    if field and field != 'None':
                        md_output += f" in {field}"
                    if sentiment:
                        md_output += f" _{sentiment}_"
                    if edu.get('sentiment_reason'):
                        md_output += f"\n  - _{edu['sentiment_reason']}_"
                    md_output += "\n"
                md_output += "\n"
            
            # Experience with Sentiment
            if background and background.get('global_experience'):
                exp_sentiment = background['global_experience']['sentiment'].upper()
                exp_reason = background['global_experience']['sentiment_reason']
                md_output += f"### Professional Experience ({exp_sentiment})\n"
                md_output += f"_{exp_reason}_\n\n"
            
            if background and background.get('experiences'):
                sorted_exp = sorted(
                    background['experiences'],
                    key=lambda x: x.get('start_date') or '',
                    reverse=True
                )
                for exp in sorted_exp:
                    title = exp.get('title', 'Unknown Role')
                    company = exp.get('company_name', 'Unknown Company')
                    sentiment = exp.get('sentiment', '').upper()
                    
                    md_output += f"- **{title}** at {company}"
                    if sentiment:
                        md_output += f" _{sentiment}_"
                    if exp.get('description') and exp['description'] != 'None':
                        md_output += f"\n  - {exp['description']}"
                    if exp.get('sentiment_reason'):
                        md_output += f"\n  - _{exp['sentiment_reason']}_"
                    md_output += "\n"
                md_output += "\n"
            
            # Highlights
            if founder.get('highlights'):
                md_output += "### Additional Highlights\n"
                for highlight in founder['highlights']:
                    if highlight.get('text'):
                        md_output += f"- {highlight['text']}\n"
                md_output += "\n"
            
            # Location
            location = founder.get('location', {}).get('location')
            if location:
                md_output += f"**Location:** {location}\n\n"
            
            md_output += "---\n\n"
            
        return md_output