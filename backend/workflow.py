import json
import re
from functools import cached_property
from urllib.parse import urlparse

from openai import AsyncOpenAI

from providers.github import GitHubClient
from providers.harmonic import HarmonicClient
from providers.predictleads.client import PredictleadsClient
from services.website_analyzer import WebsiteAnalyzer


class WebsiteAnalysisWorkflow:
    gh_repo_name: str | None = None
    gh_repo_data: dict | None = None
    gh_user_data: dict | None = None
    employees_experience: list[dict] | None = None
    technologies: list[dict] | None = None

    def __init__(self, input_string):
        self.input_string = input_string

    def _extract_domain(self):
        # Check if the input is a valid URL
        try:
            parsed_url = urlparse(self.input_string)
            domain = parsed_url.netloc
            if not domain:
                domain = parsed_url.path
            domain = domain.lower().lstrip('www.')
        except Exception as e:
            raise ValueError(f"Invalid input: {self.input_string}") from e

        # Validate domain using regex
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        )
        if not domain_pattern.match(domain):
            raise ValueError(f"Invalid domain extracted: {domain}")

        return domain

    @cached_property
    def domain(self) -> str:
        return self._extract_domain()

    async def find_github(self):
        print('Finding GitHub repo...')
        self.gh_repo_name = await PredictleadsClient().fetch_github(self.domain)
        if self.gh_repo_name:
            print(f'Found GitHub repo: {self.gh_repo_name}')
        else:
            print('No GitHub repo found')

    async def fetch_github_data(self):
        if not self.gh_repo_name:
            return
        print('Fetching GitHub data...')
        owner, repo = self.gh_repo_name.split('/')
        client = GitHubClient()
        self.gh_repo_data = await client.fetch_repo(owner, repo)
        self.gh_user_data = await client.fetch_user(owner)
        print('Fetched GitHub data')

    async def fetch_employees_experience(self):
        print('Fetching employees experience...')
        client = HarmonicClient()
        self.employees_experience = await client.find_employees_experience(self.domain)
        print('Fetched employees experience')

    async def analyze_website(self):
        print('Analyzing website...')
        analyzer = WebsiteAnalyzer('https://' + self.domain)
        await analyzer.crawl()
        print('Crawled website')
        self.technologies = await analyzer.extract_technologies()
        print('Extracted technologies')

    async def generate_memo(self):
        print('Generating memo...')

        def build_prompt():
            prompt = """
You are conducting a **Technical Due Diligence** for a venture capital firm evaluating a startup. Your task is to write a **Technical Due Diligence Memo** that provides an accessible, non-technical overview of the startup’s technology and evaluates its technological strength, maturity, and risks.

You will be provided with the following information:  
1. A list of **technologies** used by the startup, extracted from its website.  
2. A **description of the product and company**.  
3. **GitHub profile metrics** (such as stargazers, issues, pull requests, etc.).  
4. The **GitHub repository readme** to understand the codebase and documentation quality.  
5. The **GitHub user profile** to gauge the activity and credibility of key developers.  
6. The **founders' experience** in relevant technical fields.

---

### **Your memo should include the following sections:**

#### **1. Executive Summary**  
Provide a concise overview of the startup’s technical standing. Cover:  
- Is the technology stack suitable for the product they are building?  
- Does the company have a promising technical foundation?  
- Are there any red flags or risks from a technical standpoint?  

#### **2. Technology Stack Overview**  
Summarize the list of technologies used. For each technology, explain:  
- What is it used for in the startup’s product?  
- Is this technology modern, scalable, and widely adopted in the industry?  
- Are there any concerns about the technology choices (e.g., outdated tools, too niche, or too experimental)?

#### **3. GitHub Activity Analysis**  
Evaluate the startup's GitHub profile based on provided metrics:  
- Is the repository actively maintained?  
- Are there many issues and pull requests? What does that indicate about the codebase?  
- Are there any signs of a strong open-source presence or community involvement?  
- How does the quality of the **readme file** reflect the documentation standards and professionalism of the codebase?

#### **4. Developer Profiles and Founders' Experience**  
Review the experience and contributions of the key technical team members:  
- Does the founding team have a strong technical background relevant to the startup’s mission?  
- Do the GitHub profiles show significant contributions to open-source or personal projects?  
- Are there signs of innovative thinking or expertise in relevant technologies?

#### **5. Risks and Opportunities**  
Identify potential risks and opportunities from a technical perspective:  
- **Risks:** Are there any concerns regarding scalability, security, or maintainability? Are the technologies used too new or unproven?  
- **Opportunities:** Does the company have a unique technological advantage that could differentiate it in the market?

#### **6. Conclusion and Recommendation**  
Provide your overall assessment:  
- Is the startup’s technology promising and mature enough to support its growth?  
- Are there any recommendations for the VC firm to follow up on with the startup (e.g., asking for additional technical documentation, addressing specific risks)?

Make sure to use **clear, non-technical language** suitable for VC associates who may not have a technical background. Focus on providing practical insights that help them assess the startup’s technical credibility and potential risks.

--- 

**Output Format:**  
- The memo should be formatted with headers, bullet points, and concise paragraphs for readability.
- Each section should be no longer than 1-2 paragraphs to maintain brevity and clarity.
            """
            prompt += f"\n\n"
            if self.technologies:
                # TODO: Improve formatting
                fmt_technologies = json.dumps(self.technologies, indent=2, default=str)
                prompt += f"### Technologies Used:\n{fmt_technologies}\n\n"
            if self.gh_repo_data:
                # TODO: Improve formatting
                fmt_gh_repo = json.dumps(self.gh_repo_data, indent=2, default=str)
                prompt += f"### GitHub Repository Data:\n{fmt_gh_repo}\n\n"
            if self.gh_user_data:
                # TODO: Improve formatting
                fmt_gh_user = json.dumps(self.gh_user_data, indent=2, default=str)
                prompt += f"### GitHub User Data:\n{fmt_gh_user}\n\n"
            if self.employees_experience:
                # TODO: Improve formatting
                fmt_employees_experience = json.dumps(self.employees_experience, indent=2, default=str)
                prompt += f"### Employees Data:\n{fmt_employees_experience}\n\n"
            return prompt

        print()
        print(build_prompt())
        print()

        openai_client = AsyncOpenAI()
        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": build_prompt()}],
            stream=True
        )
        response_text = ''
        async for chunk in response:
            if chunk.choices[0].delta.content:
                response_text += chunk.choices[0].delta.content
        print('Generated memo')
        return response_text

    async def run_analysis(self):
        print('Starting analysis...')
        domain = self.domain
        # Find GitHub
        await self.find_github()
        # Fetch GitHub data
        await self.fetch_github_data()
        # Fetch Harmonic data
        await self.fetch_employees_experience()
        # Analyze website
        await self.analyze_website()
        # Generate memo
        memo = await self.generate_memo()
        print('Analysis complete')
        print(memo)
        with open('memo.md', 'w+') as f:
            f.write(memo)


async def main():
    workflow = WebsiteAnalysisWorkflow("https://openlit.io/")
    await workflow.run_analysis()


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    import asyncio
    asyncio.run(main())
