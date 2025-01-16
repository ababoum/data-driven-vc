import numpy as np
import datetime
import dotenv
import os
import requests
from urllib.parse import urlparse

dotenv.load_dotenv()
SIMILARWEB_API_KEY = os.getenv("SIMILARWEB_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_SEARCH_ENGINE_ID = os.getenv("GOOGLE_SEARCH_ENGINE_ID")


def url_to_domain(url):
    # Parse the URL and extract the domain name
    parsed_url = urlparse(url)
    return parsed_url.netloc or parsed_url.path


def find_url_for_keyword(keyword):
    api_key = GOOGLE_API_KEY
    cse_id = GOOGLE_SEARCH_ENGINE_ID
    
    search_url = f"https://www.googleapis.com/customsearch/v1?q={keyword}&key={api_key}&cx={cse_id}"
    
    response = requests.get(search_url)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        return None

    data = response.json()
    
    # Get the first search result
    if 'items' in data:
        first_result = data['items'][0]['link']
        return first_result
    
    return None


def analyze_visits(response_json):
    # Extract visits data
    visits = [entry['visits'] for entry in response_json['visits']]

    # Latest number of visits
    latest_visits = visits[-1]

    # Calculate the trend using the slope of a linear fit
    slope = np.polyfit(range(len(visits)), visits, 1)[0]

    # Determine the trend
    if slope > 0:
        trend = "ascending"
    elif slope < 0:
        trend = "descending"
    else:
        trend = "flat"

    return int(latest_visits), trend


def get_trends(tech_name):
    tech_url = find_url_for_keyword(tech_name)
    print(tech_url)
    domain = url_to_domain(tech_url)
    start_date = (datetime.datetime.now() -
                  datetime.timedelta(days=395)).strftime("%Y-%m")
    end_date = (datetime.datetime.now() -
                datetime.timedelta(days=30)).strftime("%Y-%m")
    url = f"https://api.similarweb.com/v1/website/{domain}/total-traffic-and-engagement/visits?api_key={SIMILARWEB_API_KEY}&start_date={
        start_date}&end_date={end_date}&country=world&granularity=monthly&main_domain_only=false&format=json&show_verified=false&mtd=false&engaged_only=false"

    headers = {
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    return analyze_visits(response.json())


if __name__ == "__main__":
    techs = ["AWS GLUE", "Kubernetes", "Docker", "React", "Angular", "Vue.js"]
    ret = dict()
    for tech in techs:
        try:
            ret[tech] = get_trends(tech)
        except Exception as e:
            print(f"Failed to get trends for {tech}: {e}")
    print(ret)
