from openai import OpenAI
import json
import os

openai_client = OpenAI()

def wrap_triple_quotes(text: str):
    return f"```\n{text}\n```"

def extract_relevant_pages_url(webpage_urls: list[str]):
    formatted_urls = '\n'.join([f"- {url}" for url in webpage_urls])
    messages = [
        {"role": "developer", "content": "You are a VC analyst, your role is to investigate and rationalize an investment decision on a company. You will be feeded with a list of URLs of all the pages of the company website. Your task is to identify the most relevant url to extract information from. Knowing that those relevant urls will be used to extract information about the company, its founders, its team members, its product, its business and its underlying technologies."},
        {"role": "user", "content": f"""
{formatted_urls}
"""}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            }
                        }
                    }
                }
            }
        }
    )

    completion = response.choices[0].message.content
    try:
        parsed_completion = json.loads(completion)
        return parsed_completion.get('urls')
    except Exception as e:
        print(e)


def generate_company_tech_summary(company = None, webpages: dict = None, domain: str = None, main_techs: list = None, specific_techs: list = None):
    if not domain:
        raise Exception("Please provide a domain")

    if not company:
        raise Exception("Please provide a company object")

    if not webpages:
        raise Exception("Please provide a webpages object")

    relevant_pages = extract_relevant_pages_url(webpages.keys())

    company_description_prompt = ''
    if company.get('description'):
        company_description_prompt = f"company description:\n{wrap_triple_quotes(company.get('description'))}"

    webpages_prompt = ''
    if relevant_pages and len(relevant_pages) > 0:
        for page in relevant_pages:
            webpage_content = webpages.get(page)
            webpages_prompt += f"- {page}:\n{wrap_triple_quotes(webpage_content)}\n"
        webpages_prompt = f"web pages:\n{webpages_prompt}"

    messages = [
        {"role": "developer", "content": "You are a VC analyst, your role is to investigate and rationalize an investment decision on a company. You will be provided the scraped data of multiple pages of the company website. You may also receive list of main technologies and/or specific technologies that many other vc analysts may not understand. You will be also provided with the company basic description. Your task is to generate a short summary of the company for the non technical VC what is the company about, what may be so special about the used technologies if relevant or uncommon, its business model."},
        {"role": "user", "content": f"""

{company_description_prompt}
{webpages_prompt}
{'main technologies: ' + ', '.join(main_techs) if main_techs else ''}
{'specific technologies: ' + ', '.join(main_techs) if main_techs else ''}
"""}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "data",
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {
                            "type": "string"
                        }
                    }
                }
            }
        }
    )

    completion = response.choices[0].message.content
    try:
        parsed_completion = json.loads(completion)
        return parsed_completion.get('summary')
    except Exception as e:
        print(e)
        return None