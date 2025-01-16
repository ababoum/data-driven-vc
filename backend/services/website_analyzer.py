import asyncio
import json
import os

from firecrawl import FirecrawlApp
from openai import AsyncOpenAI


class WebsiteAnalyzer:
    def __init__(self, url: str, fc_api_key: str = None):
        self.url = url
        self.fc_app = FirecrawlApp(api_key=fc_api_key or os.getenv('FIRECRAWL_API_KEY'))
        self.openai_client = AsyncOpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self._webpages = {}

    async def crawl(self):
        crawl_result = self.fc_app.async_crawl_url(self.url, params={
            'limit': 5,
            'scrapeOptions': {'formats': ['markdown']}
        })
        task_id = crawl_result['id']
        while crawl_result.get('status', 'scraping') == 'scraping':
            crawl_result = self.fc_app.check_crawl_status(task_id)
            await asyncio.sleep(1.0)
        self._webpages = {
            page['metadata']['sourceURL']: page['markdown'] for page in crawl_result['data']
        }

    @property
    def formatted_webpages(self) -> str:
        max_chars = 100000
        fmt_webpages = ''
        for url, markdown in self._webpages.items():
            fmt_webpages += f"## {url}\n{markdown}\n\n"
        return fmt_webpages[:max_chars]

    async def extract_technologies(self) -> list[dict]:
        def build_prompt():
            prompt = (
                    "You are an AI assistant tasked with analyzing the content of a startup's website. "
                    "The goal is to identify the list of technologies used by this startup to build its products, infrastructure, and services. "
                    "If have not find any technologies, please return an empty list.\n\n"
                    "The input is a collection of pages in Markdown format. Your response should be in the following structured JSON format:\n\n"
                    "{\n"
                    "  'technologies': [\n"
                    "    { 'name': '<technology_name>', 'category': '<category>' }\n"
                    "  ]\n"
                    "}\n\n"
                    "Categories can include: Programming Languages, Frameworks, Libraries, Databases, Cloud Platforms, DevOps Tools, etc.\n\n"
                    "Here is the content of the website:\n\n"
                    + self.formatted_webpages
                    + "\n\nPlease analyze and return the JSON output."
            )
            return prompt

        # Send the prompt to OpenAI's model
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": build_prompt()}],
            response_format={"type": "json_object"}
        )
        content = response.choices[0].message.content
        return json.loads(content).get('technologies')


async def main():
    website_url = 'https://twenty.com/'

    analyzer = WebsiteAnalyzer(website_url)

    # Step 1: Crawl the website
    await analyzer.crawl()

    # Step 2: Extract technologies using ChatGPT
    print(await analyzer.extract_technologies())


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(main())
