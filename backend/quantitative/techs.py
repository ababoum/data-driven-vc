from tech_trends import get_trends
import google.generativeai as genai
import json
import os

import dotenv
from openai import AsyncOpenAI

from providers.harmonic import HarmonicClient
from providers.predictleads.client import PredictleadsClient

dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


async def oa_sum_technologies(techs: list):
    response = await AsyncOpenAI().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
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

    ret["specific_techs"] = (await oa_sum_technologies(tech_names)).split(",")
    return ret


async def get_all_techs_with_trends(domain_name):
    techs_list = get_techs(domain_name)
    specific_techs = techs_list["specific_techs"]
    techs_list["specific_techs"] = list()
    for tech in specific_techs:
        techs_list["specific_techs"] += [{"name": tech,
                                          "stats": get_trends(tech)}]
    return json.dumps(techs_list)


async def main():

    print(await get_all_techs_with_trends("stripe.com"))
    exit()

    try:
        domain = "stripe.com"

        print(get_techs(domain))

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
