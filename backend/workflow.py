import json
import re
from urllib.parse import urlparse

from openai import AsyncOpenAI

from providers.harmonic import HarmonicClient
from services.code_analyzer import CodeQualityAnalyzer
from services.github_analyzer import GitHubAnalyzer
from services.website_analyzer import WebsiteAnalyzer


class WebsiteAnalysisWorkflow:
    gh_report: str | None = None
    code_report: str | None = None
    employees_experience: list[dict] | None = None
    technologies: list[dict] | None = None

    def __init__(self, input_string: str):
        self.domain = self._extract_domain(input_string)
        self.gh_analyzer = GitHubAnalyzer(self.domain)

    @staticmethod
    def _extract_domain(input_string: str):
        # Check if the input is a valid URL
        try:
            parsed_url = urlparse(input_string)
            domain = parsed_url.netloc
            if not domain:
                domain = parsed_url.path
            domain = domain.lower().lstrip('www.')
        except Exception as e:
            raise ValueError(f"Invalid input: {input_string}") from e

        # Validate domain using regex
        domain_pattern = re.compile(
            r'^(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$'
        )
        if not domain_pattern.match(domain):
            raise ValueError(f"Invalid domain extracted: {domain}")

        return domain

    async def generate_competitors_report(self) -> dict:
        harmonic_client = HarmonicClient()
        company = await harmonic_client.find_company(self.domain)
        competitors = await harmonic_client.get_competitors(self.domain)
        md_competitors = harmonic_client.format_companies_to_md(competitors)
        outliers_good = harmonic_client.find_outliers(company, competitors, 0.2)
        outliers_bad = harmonic_client.find_outliers(company, competitors, 0.5)
        performance = -1  # Default performance
        if any(outlier.get('entity_urn') == company.get('entity_urn') for outlier in outliers_good):
            performance = 1
            performance_comment = "This company outperforms its competitors !"
        elif any(outlier.get('entity_urn') == company.get('entity_urn') for outlier in outliers_bad):
            performance = 0
            performance_comment = "This company shows average performance compared to competitors"
        else:
            performance_comment = "This company underperforms compared to its competitors"

        step_data = {
            "step": 1,
            "_title": "Competitors Analysis",
            "competitors": md_competitors,
            "overperformers": [company["name"] for company in outliers_good],
            "performance_comment": performance_comment,
            "_performance": performance,
            "calculation_explanation": """The competitor analysis is performed using multiple data points and sophisticated algorithms:

        1. Company Identification:
           - First, we identify direct and indirect competitors using the Harmonic API
           - Companies are matched based on industry, market segment, and business model

        2. Performance Metrics:
           - Headcount growth rate and current size
           - Funding history and total raised amount
           - Market presence and geographic expansion
           - Customer base and market share

        3. Outlier Detection:
           - We use an Isolation Forest algorithm to detect companies that significantly deviate from the norm
           - The algorithm considers multiple dimensions simultaneously
           - Companies in the top 20% are marked as overperformers (green)
           - Companies in the bottom 50% are marked as underperformers (red)
           - Others are considered average performers (yellow)

        4. Final Score Calculation:
           - Each metric is weighted based on its importance
           - Growth metrics are given higher weight than absolute numbers
           - Recent performance is weighted more heavily than historical data"""
        }
        return step_data

    async def generate_github_report(self) -> dict:
        await self.gh_analyzer.run_analysis()
        self.gh_report = self.gh_analyzer.report
        performance = self.gh_analyzer.color
        report = self.gh_analyzer.report

        performance_comment = {
            1: "Strong repository activity and community engagement",
            0: "Average repository performance and community engagement",
            -1: "Weak repository activity and community engagement"
        }[performance]

        step_data = {
            "step": 2,
            "_title": "GitHub Metrics Analysis",
            "Metrics": report,
            "_performance": performance,
            "performance_comment": performance_comment,
            "calculation_explanation": """
1. **Stars Growth Rate**: Reflects repository **popularity** over time.  
2. **Forks Count**: Shows **external interest** in adapting or contributing to the code.  
3. **Commit Frequency**: Indicates **active development** and maintenance.  
4. **Contributors Count**: Highlights **team/community engagement**.  
5. **Issue Resolution Time**: Measures **responsiveness** to bugs and requests.  
"""
        }
        return step_data

    async def generate_code_quality_report(self) -> dict:
        if not self.gh_analyzer.owner:
            report = 'No GitHub repository found.'
            performance = -1
        else:
            analyzer = CodeQualityAnalyzer(self.gh_analyzer.owner, self.gh_analyzer.repo)
            analyzer.run_analysis()
            self.code_report = analyzer.report
            performance = analyzer.color
            report = analyzer.report

        performance_comment = {
            1: "Great code quality and documentation",
            0: "Average code quality and documentation",
            -1: "Weak code quality and documentation"
        }[performance]

        step_data = {
            "step": 3,
            "_title": "Code Quality Analysis",
            "Report": report,
            "_performance": performance,
            "performance_comment": performance_comment,
        }
        return step_data

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
            if self.gh_report:
                prompt += f"### GitHub Report:\n{self.gh_report}\n\n"
            if self.code_report:
                prompt += f"### GitHub User Data:\n{self.code_report}\n\n"
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
