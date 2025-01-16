from collections import defaultdict
import json
from openai import OpenAI
import os

openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

def wrap_triple_quotes(text: str):
    return f"```\n{text}\n```"

def enhance_founder_background(company_prompt: str = None, experience_prompt: str = None, education_prompt: str = None, tags_prompt: str = None):
    messages = [
        {"role": "developer", "content": "You are a VC analyst, your role is to investigate and rationalize an investment decision on a company. To do so, you have to qualify each experience and education of the current startup founder. Given the startup description, tags and experience and education background of the founder."},
        {"role": "user", "content": f"""
{company_prompt}
{tags_prompt}
{experience_prompt}
{education_prompt}
"""}
    ]

    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "educations",
                "schema": {
                    "type": "object",
                    "properties": {
                        "educations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "start_date": {
                                        "type": "string"
                                    },
                                    "end_date": {
                                        "type": "string"
                                    },
                                    "school_name": {
                                        "type": "string"
                                    },
                                    "field": {
                                        "type": "string"
                                    },
                                    "degree": {
                                        "type": "string"
                                    },
                                    "sentiment": {
                                        "type": "string",
                                        "enum": ["outstanding", "positive", "kinda positive", "neutral", "negative"]
                                    },
                                    "sentiment_reason": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "start_date",
                                    "end_date",
                                    "sentiment",
                                    "school_name",
                                    "degree",
                                    "sentiment_reason"
                                ]
                            }
                        },
                        "experiences": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "start_date": {
                                        "type": "string"
                                    },
                                    "end_date": {
                                        "type": "string"
                                    },
                                    "company_name": {
                                        "type": "string"
                                    },
                                    "title": {
                                        "type": "string"
                                    },
                                    "role_type": {
                                        "type": "string"
                                    },
                                    "department": {
                                        "type": "string"
                                    },
                                    "description": {
                                        "type": "string"
                                    },
                                    "sentiment": {
                                        "type": "string",
                                        "enum": ["outstanding", "positive", "kinda positive", "neutral", "negative"]
                                    },
                                    "sentiment_reason": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "start_date",
                                    "end_date",
                                    "title",
                                    "company_name",
                                    "role_type",
                                    "department",
                                    "description",
                                    "sentiment",
                                    "sentiment_reason"
                                ]
                            }
                        },
                        "global": {
                            "type": "object",
                            "description": "Global sentiment of the founder based on all experiences and educations",
                            "properties": {
                                "sentiment": {
                                    "type": "string",
                                    "enum": ["outstanding", "positive", "kinda positive", "neutral", "negative"]
                                },
                                "sentiment_reason": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "sentiment",
                                "sentiment_reason"
                            ]
                        },
                        "global_experience": {
                            "type": "object",
                            "description": "Global sentiment all experiences of the founder",
                            "properties": {
                                "sentiment": {
                                    "type": "string",
                                    "enum": ["outstanding", "positive", "kinda positive", "neutral", "negative"]
                                },
                                "sentiment_reason": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "sentiment",
                                "sentiment_reason"
                            ]
                        },
                        "global_education": {
                            "type": "object",
                            "description": "Global sentiment of all education of the founder",
                            "properties": {
                                "sentiment": {
                                    "type": "string",
                                    "enum": ["outstanding", "positive", "kinda positive", "neutral", "negative"]
                                },
                                "sentiment_reason": {
                                    "type": "string"
                                }
                            },
                            "required": [
                                "sentiment",
                                "sentiment_reason"
                            ]
                        },
                    },
                }
            }
        }
    )

    completion = response.choices[0].message.content
    try:
        parsed_completion = json.loads(completion)
        return parsed_completion
    except Exception as e:
        print(e)


def qualify_founder(company: any = None, founder: any = None):
    tags_prompt: str = ''

    if 'tags_v2' in company:
        tags_prompt = ''
        tags_by_type = defaultdict(list)
        for tag in company['tags_v2']:
            tags_by_type[tag['type']].append(tag['display_value'])

        tags_types = ['INDUSTRY', 'TECHNOLOGY', 'PRODUCT_TYPE', 'CUSTOMER_TYPE', 'MARKET_VERTICAL', 'TECHNOLOGY_TYPE']

        for tag_type in tags_types:
            tags = tags_by_type.get(tag_type)
            if tags:
                joined_tags = ', '.join(tags)
                tags_prompt += f"{tag_type}: {joined_tags}\n"

    if (tags_prompt):
        tags_prompt = f"tags:\n{wrap_triple_quotes(tags_prompt)}"

    if 'education' in founder:
        education_prompt = ''
        educations = founder.get('education')

        for education in educations:
            school = education.get('school')
            school_name = school.get('name') if school else None
            degree = education.get('degree')
            field = education.get('field')
            degree = education.get('degree')
            start_date = education.get('start_date')
            end_date = education.get('end_date')

            education_prompt += f"""
school name: {school_name}
degree: {degree}
field: {field}
start date: {start_date}
end date: {end_date}
"""

        education_prompt = f"""educations:
{wrap_triple_quotes(education_prompt)}
"""

    if 'experience' in founder:
        experiences = founder.get('experience')

        experience_prompt = ''

        for experience in experiences:
            title = experience.get('title')
            department = experience.get('department')
            description = experience.get('description')
            role_type = experience.get('role_type')
            company_name = experience.get('company_name')
            start_date = experience.get('start_date')
            end_date = experience.get('end_date')

            experience_prompt += f"""
company name: {company_name}
title: {title}
role type: {role_type}
department: {department}
experience description: {description}
start date: {start_date}
end date: {end_date}
"""

        experience_prompt = f"""experiences:
    {wrap_triple_quotes(experience_prompt)}
    """

    company_prompt = f"""
startup description:
{wrap_triple_quotes(company['description'])}
"""

    # print(company_prompt, experience_prompt, education_prompt, tags_prompt)
    return enhance_founder_background(company_prompt=company_prompt, experience_prompt=experience_prompt, education_prompt=education_prompt, tags_prompt=tags_prompt)