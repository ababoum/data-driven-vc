import asyncio

import json
import re
import asyncio
from urllib.parse import urlparse

from openai import AsyncOpenAI

from providers.harmonic import HarmonicClient
from services.code_analyzer import CodeQualityAnalyzer
from services.github_analyzer import GitHubAnalyzer
from services.website_analyzer import WebsiteAnalyzer
from cache import memorize
from qualitative.founders import qualify_founder
from quantitative.techs import get_all_techs_with_trends, get_techs
from qualitative.short_tech_summary import generate_company_tech_summary
class WebsiteAnalysisWorkflow:
    gh_report: str | None = None
    code_report: str | None = None
    employees_experience: list[dict] | None = None
    technologies: list[dict] | None = None
    founders_report: str | None = None

    def __init__(self, input_string: str):
        self.domain = self._extract_domain(input_string)
        self.gh_analyzer = GitHubAnalyzer(self.domain)

    def __str__(self):
        return f"WebsiteAnalysisWorkflow(domain={self.domain})"

    def __repr__(self):
        return str(self)

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

    @memorize()
    async def generate_competitors_report(self) -> dict:
        harmonic_client = HarmonicClient()
        company = await harmonic_client.find_company(self.domain)
        competitors = await harmonic_client.get_competitors(self.domain)
        md_competitors = harmonic_client.format_companies_to_md(competitors)
        outliers_good, importance_good = harmonic_client.find_outliers(company, competitors, 0.2)
        outliers_bad, importance_bad = harmonic_client.find_outliers(company, competitors, 0.5)

        # Calculate performance based on whether the company is in outliers
        performance = -1  # Default performance
        if any(outlier.get('entity_urn') == company.get('entity_urn') for outlier in outliers_good):
            performance = 1
            performance_comment = "This company outperforms its competitors !"
            importance = importance_good
        elif any(outlier.get('entity_urn') == company.get('entity_urn') for outlier in outliers_bad):
            performance = 0
            performance_comment = "This company shows average performance compared to competitors"
            importance = importance_bad
        else:
            performance_comment = "This company underperforms compared to its competitors"
            importance = importance_bad

        # Format the importance metrics for display
        importance_md = ""
        for metric, value in sorted(importance.items(), key=lambda x: x[1], reverse=True):
            formatted_metric = metric.replace('_', ' ').title()
            importance_md += f"- **{formatted_metric}**: {value}% impact on the analysis\n"

        step_data = {
            "step": 4,
            "_title": "Competitors Analysis",
            "competitors": md_competitors,
            "overperformers": [company["name"] for company in outliers_good],
            "performance_comment": performance_comment,
            "importance_metrics": importance_md,
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
           - Each metric is weighted based on its importance (shown in Key Metrics Impact)
           - Growth metrics are given higher weight than absolute numbers
           - Recent performance is weighted more heavily than historical data"""
        }
        return step_data

    @memorize()
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

    @memorize()
    async def generate_code_quality_report(self) -> dict:
        try:
            if not self.gh_analyzer.owner:
                report = 'No GitHub repository found.'
                performance = -1
            else:
                analyzer = CodeQualityAnalyzer(self.gh_analyzer.owner, self.gh_analyzer.repo)
                await asyncio.to_thread(analyzer.run_analysis)
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
            
        except Exception:
            return {
                "step": 3,
                "_title": "Code Quality Analysis",
                "Report": f"Error analyzing code quality: Access to GitHub repository denied",
                "_performance": 0,
                "performance_comment": "Analysis failed"
            }

    @memorize()
    async def generate_founders_report(self) -> dict:
        try:
            harmonic_client = HarmonicClient()
            company = await harmonic_client.find_company(self.domain)
            founders = await harmonic_client.get_founders_from_company(company)
            founders_backgrounds = []
            for founder in founders:
                founder_background = qualify_founder(company, founder)
                founders_backgrounds.append(founder_background)
            founders_md = harmonic_client.format_founders_to_md(founders, founders_backgrounds)

            # Calculate performance based on founders' sentiments
            sentiment_scores = {
                'outstanding': 1,
                'positive': 0.5, 
                'neutral': 0,
                'negative': -0.5,
                'concerning': -1
            }

            total_score = 0
            for background in founders_backgrounds:
                if background and background.get('global', {}).get('sentiment'):
                    total_score += sentiment_scores.get(background['global']['sentiment'].lower(), 0)

            # Calculate average and determine performance
            avg_score = total_score / len(founders_backgrounds) if founders_backgrounds else 0
            performance = 1 if avg_score > 0.5 else (-1 if avg_score < -0.25 else 0)

            # Generate performance comment based on score
            if performance == 1:
                performance_comment = "Exceptional founding team with outstanding backgrounds and highly relevant experience"
            elif performance == 0:
                performance_comment = "Solid founding team with good experience and relevant backgrounds"
            else:
                performance_comment = "Founding team shows some areas of concern that may need further evaluation"

            step_data = {
                "step": 1,
                "_title": "Founder Analysis",
                "founders": founders_md,
                "_performance": performance,
                "performance_comment": performance_comment,
                "calculation_explanation": """The founder analysis is performed through a comprehensive evaluation of multiple factors:

1. Overall Assessment:
   - Each founder's background is analyzed for their experience, education, and achievements
   - Sentiment analysis is performed on their background (Outstanding, Positive, Neutral, Negative, or Concerning)
   - The analysis considers the relevance of their experience to the current venture

2. Educational Background:
   - Quality and prestige of educational institutions
   - Relevance of degrees to the company's domain
   - Additional certifications and specialized training

3. Professional Experience:
   - Previous founding experience and exits
   - Industry-relevant positions and achievements
   - Leadership roles and responsibilities
   - Track record of success in similar domains

4. Final Score Calculation:
   - Each founder's sentiment is converted to a numerical score:
     * Outstanding = 1.0
     * Positive = 0.5
     * Neutral = 0.0
     * Negative = -0.5
     * Concerning = -1.0
   - The average score across all founders determines the final performance:
     * High Performance (Green): Average score > 0.5
     * Average Performance (Yellow): Average score between -0.25 and 0.5
     * Concerning Performance (Red): Average score < -0.25"""
            }
            self.founders_report = step_data
            return step_data

        except Exception as e:
            return {
                "step": 1,
                "_title": "Founder Analysis",
                "founders": "Error analyzing founders",
                "_performance": 0,
                "performance_comment": "Analysis failed",
                "calculation_explanation": str(e)
            }
            
    @memorize()
    async def generate_tech_summary_report(self) -> dict:
        harmonic_client = HarmonicClient()
        analyzer = WebsiteAnalyzer('https://' + self.domain)
        await analyzer.crawl()
        techs = await get_techs(self.domain)
        summary = generate_company_tech_summary(company= await harmonic_client.find_company(self.domain), webpages=analyzer._webpages, domain=self.domain, main_techs=techs.get('main_techs'), specific_techs=techs.get('specific_techs'))
        return {
            "step": 0,
            "_title": "Tech Summary",
            "tech_summary": summary,
            "performance_comment": "",
        }

    @memorize()
    async def generate_tech_trends_report(self) -> dict:
        try:
            techs = await get_all_techs_with_trends(self.domain)
            techs_dict = json.loads(techs)

            # Calculate performance based on tech trends
            performance = 0
            total_techs = len(techs_dict["specific_techs"])
            ascending_count = 0

            for tech in techs_dict["specific_techs"]:
                if tech["stats"]["trend"] == "ascending":
                    ascending_count += 1

            if total_techs > 0:
                ascending_ratio = ascending_count / total_techs
                if ascending_ratio >= 0.7:
                    performance = 1
                elif ascending_ratio >= 0.4:
                    performance = 0.5
                else:
                    performance = 0

            performance_comment = ""
            if performance == 1:
                performance_comment = "Strong technology choices with positive adoption trends"
            elif performance == 0.5:
                performance_comment = "Mixed technology stack with some trending and some stable technologies"
            else:
                performance_comment = "Technology stack shows declining adoption trends"

            step_data = {
                "step": 0,
                "_title": "Technology Trends Analysis",
                "company_name": techs_dict["company_name"],
                "description": techs_dict["description"],
                "main_techs": techs_dict["main_techs"],
                "specific_techs": techs_dict["specific_techs"],
                "_performance": performance,
                "performance_comment": performance_comment
            }
            return step_data

        except Exception as e:
            return {
                "step": 0,
                "_title": "Technology Trends Analysis",
                "company_name": "Error analyzing tech trends",
                "description": str(e),
                "main_techs": [],
                "specific_techs": [],
                "_performance": 0,
                "performance_comment": "Analysis failed"
            }

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
- The memo should be formatted in .md format with headers, bullet points, and concise paragraphs for readability.
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
            # add step 4 data
            if self.founders_report:
                prompt += f"### Founders Data:\n{self.founders_report}\n\n"
            return prompt

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
        
        return {
                "step": 5,
                "_title": "Memo of the entire analysis",
                "memo": response_text,
                "calculation_explanation": "This memo was generated using ChatGPT-4o"
            }
        
    async def run_analysis(self):
        print('Starting analysis...')
        domain = self.domain
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
    asyncio.run(main())
