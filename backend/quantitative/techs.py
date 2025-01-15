import json
import requests
import dotenv
import os

dotenv.load_dotenv()
PL_AUTH_KEY = os.getenv("PL_AUTH_KEY")
PL_AUTH_TOKEN = os.getenv("PL_AUTH_TOKEN")
HARMONIC_API_KEY = os.getenv("HARMONIC_API_KEY")
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
    url = f"https://predictleads.com/api/v3/companies/{
        domain_name}/technology_detections?limit=50"
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
            {
                "role": "system",
                "content": "You are a helpful assistant, that knows a lot of technologies used by startups."
            },
            {
                "role": "user",
                "content": f"Pick 5 main technologies from the ones listed below. Return the keywords separated by a comma and nothing else. Here are the technologies: {techs}"
            }
        ]
    }
    response = requests.post(url, headers=headers, json=data)

    # Check if the request was successful
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        print("Error:", response.status_code, response.text)


def get_techs(domain_name):
    ret = dict()
    h_company = h_get_company(domain_name)
    pl_company = pl_get_company(domain_name)["data"][0]["attributes"]
    
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
    techs = pl_get_technologies(domain_name)
    tech_names = []
    tech_ids = [tech['relationships']['technology']['data']['id']
                for tech in techs.get("data", [])]
    for tech_id in tech_ids:
        tech_name = pl_get_tech_name(tech_id)
        tech_names.append(tech_name["data"][0]["attributes"]["name"])
    
    ret["specific_techs"] = oa_sum_technologies(tech_names).split(", ")
    return json.dumps(ret)
    

if __name__ == "__main__":
    try:
        domain = "stripe.com"
        
        print(get_techs(domain))
        exit()

        h_company = h_get_company(domain)
        pl_company = pl_get_company(domain)["data"][0]["attributes"]

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

        techs = pl_get_technologies(domain)
        tech_ids = [tech['relationships']['technology']['data']['id']
                    for tech in techs.get("data", [])]
        list_of_techs = []
        for tech_id in tech_ids:
            tech_name = pl_get_tech_name(tech_id)
            # list_of_techs += tech_name["data"][0]["attributes"]["categories"]
            list_of_techs += [tech_name["data"][0]["attributes"]["name"]]

        oa_sum_technologies(list_of_techs)

    except Exception as e:
        print(f"An error occurred: {e}")
