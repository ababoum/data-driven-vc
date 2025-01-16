import json
import os

import dotenv
from openai import AsyncOpenAI

from providers.harmonic import HarmonicClient
from providers.predictleads.client import PredictleadsClient

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def pl_get_company(domain_name):
    url = f"https://predictleads.com/api/v3/companies/{domain_name}"
    headers = {
        "X-Api-Key": PL_AUTH_KEY,
        "X-Api-Token": PL_AUTH_TOKEN,
    }
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def h_get_company(domain_name):
    url = f"https://api.harmonic.ai/companies"
    headers = {
        "apikey": HARMONIC_API_KEY,
    }
    params = {
        "website_domain": domain_name
    }

    response = requests.post(url, headers=headers, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def pl_get_technologies(domain_name):
    url = f"https://predictleads.com/api/v3/companies/{domain_name}/technology_detections?limit=50"
    headers = {
        "X-Api-Key": PL_AUTH_KEY,
        "X-Api-Token": PL_AUTH_TOKEN,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def pl_get_tech_name(tech_id):
    url = f"https://predictleads.com/api/v3/technologies/{tech_id}"

    headers = {
        "X-Api-Key": PL_AUTH_KEY,
        "X-Api-Token": PL_AUTH_TOKEN,
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        response.raise_for_status()


def oa_sum_technologies(techs: list):

    url = "https://api.openai.com/v1/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
#async def oa_sum_technologies(techs: list):
#    response = await AsyncOpenAI().chat.completions.create(
#        model="gpt-4o-mini",
#        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant, that knows a lot of technologies used by startups."
            },
            {
                "role": "user",
                "content": f"Pick 5 main technologies from the ones listed below. Return the keywords separated by a comma and nothing else. Here are the technologies: {techs}"
            }
        ]
    )
    return response.choices[0].message.content


async def get_techs(domain_name: str):
    ret = dict()
    pl_client = PredictleadsClient()
    h_company = await HarmonicClient().find_company(domain_name)
    pl_company = (await pl_client.fetch_company(domain_name))["data"][0]["attributes"]
    
    ret["company_name"] = pl_company["company_name"]
    ret["title"] = pl_company["meta_title"]
    ret["description"] = pl_company["meta_description"]
    ret["main_techs"] = []
    
    for item in h_company["tags_v2"]:
        if item["type"] == "TECHNOLOGY_TYPE":
            ret["main_techs"].append(item["display_value"])
    for item in h_company["tags"]:
        if item["type"] == "TECHNOLOGY":
            ret["main_techs"].append(item["display_value"])
            
    ret["specific_techs"] = []
    techs = await pl_client.fetch_technologies(domain_name)
    tech_names = []
    tech_ids = [tech['relationships']['technology']['data']['id']
                for tech in techs.get("data", [])]
    for tech_id in tech_ids:
        tech_name = await pl_client.fetch_tech_name(tech_id)
        tech_names.append(tech_name["data"][0]["attributes"]["name"])
    
    ret["specific_techs"] = (await oa_sum_technologies(tech_names)).split(", ")
    return json.dumps(ret)
    

async def main():
    try:
        domain = "stripe.com"

        print(await get_techs(domain))
        exit()

        pl_client = PredictleadsClient()
        h_company = await HarmonicClient().find_company(domain)
        pl_company = (await pl_client.fetch_company(domain))["data"][0]["attributes"]

        print(pl_company["company_name"])
        print(pl_company["meta_title"])
        print(pl_company["meta_description"])
        print('*' * 50)

        print("Main technologies used by the company:")
        for item in h_company["tags_v2"]:
            if item["type"] == "TECHNOLOGY_TYPE":
                print("   ", item["display_value"])
        for item in h_company["tags"]:
            if item["type"] == "TECHNOLOGY":
                print("   ", item["display_value"])

        print('*' * 50)

        print("Specific technologies used by the company:")

        techs = await pl_client.fetch_technologies(domain)
        tech_ids = [tech['relationships']['technology']['data']['id']
                    for tech in techs.get("data", [])]
        list_of_techs = []
        for tech_id in tech_ids:
            tech_name = await pl_client.fetch_tech_name(tech_id)
            # list_of_techs += tech_name["data"][0]["attributes"]["categories"]
            list_of_techs += [tech_name["data"][0]["attributes"]["name"]]

        await oa_sum_technologies(list_of_techs)

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
