import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict
import os
#from openai import OpenAI

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from providers.harmonic.client import HarmonicClient
from qualitative.founders import qualify_founder

from models import DomainRequest, StepSummaryRequest, JobResponse, JobStatus
from dotenv import load_dotenv

load_dotenv("../.env", override=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
from utils import get_gpt_summary
from workflow import WebsiteAnalysisWorkflow

# In-memory job store
jobs: Dict[str, JobStatus] = {}


load_dotenv()
app = FastAPI(title="Data Driven VC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def format_step_data(step_data: dict) -> str:
    """Format step data into a readable text."""
    title = step_data.get("title", "Analysis Step")
    
    # Remove step number from the data to display
    data_to_display = {k: v for k, v in step_data.items() if k != "step"}
    
    # Create a formatted string with the step title and data
    formatted_text = f"{title}:\n"
    for key, value in data_to_display.items():
        formatted_key = key.replace('_', ' ').title()
        formatted_text += f"- {formatted_key}: {value}\n"
    
    return formatted_text

#async def get_gpt_summary(text: str) -> str:
#    """Get summary from ChatGPT."""
#    try:
#        #return api_key
#        if not OPENAI_API_KEY:
#            raise ValueError("OPENAI_API_KEY environment variable is not set")
#            
#        client = OpenAI(api_key=OPENAI_API_KEY)
#        prompt = f"Explain this to me in details in markdown format by always keeping your answer objective and concise and by assuming I'm a VC who doesn't know anything about tech (Always try to comment on how it could be a pro or a con in the context of a future investment): {text}"
#        
#        response = await asyncio.to_thread(
#            lambda: client.chat.completions.create(
#                model="gpt-4o-mini",
#                messages=[
#                    {"role": "user", "content": prompt}
#                ]
#            )
#        )
#        
#        return response.choices[0].message.content
#    except Exception as e:
#        print(f"Error calling ChatGPT API: {str(e)}")
#        return f"Failed to generate summary: {str(e)}"

async def process_domain(domain: str, job_id: str):
    try:
        harmonic_client = HarmonicClient()
        # Step 1: Competitors
        company = await harmonic_client.find_company(domain)
        competitors = await harmonic_client.get_competitors(domain)
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
            "step": 1,
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
        jobs[job_id].status = "Analyzing competitors..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 2: GitHub Analysis
        workflow = WebsiteAnalysisWorkflow(domain)

        jobs[job_id].status = "Analyzing GitHub..."
        report, performance = await workflow.generate_github_report()
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

        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        ## Step 3: Code Quality
        #jobs[job_id].status = "Analyzing code quality..."
        #report, performance = await workflow.generate_code_quality_report()
        #performance_comment = {
        #    1: "Great code quality and documentation",
        #    0: "Average code quality and documentation",
        #    -1: "Weak code quality and documentation"
        #}[performance]
#
        #step_data = {
        #    "step": 3,
        #    "_title": "Code Quality Analysis",
        #    "Report": report,
        #    "_performance": performance,
        #    "performance_comment": performance_comment,
        #}
#
        #jobs[job_id].current_step_data = step_data
        #jobs[job_id].step_history.append(step_data)
        #await asyncio.sleep(1)

        # Step 4: Founder Analysis
        
        founders = await harmonic_client.get_founders_from_company(company)
        founders_backgrounds = []
        for founder in founders:
            founder_background = qualify_founder(company, founder, OPENAI_API_KEY)
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
            "step": 4,
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
        jobs[job_id].status = "Analyzing founders..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 5: Key People
        step_data = {
            "step": 5,
            "_title": "TODO",
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": "f",
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 6: Market analysis
        step_data = {
            "step": 6,
            "_title": "TODO",
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 7: Financial assessment
        step_data = {
            "step": 7,
            "_title": "TODO",
            "revenue_range": f"${random.randint(1, 50)}M - ${random.randint(51, 100)}M",
            "funding_rounds": random.randint(1, 5),
            "burn_rate": f"${random.randint(100, 999)}K/month"
        }
        jobs[job_id].status = "Evaluating financial metrics..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 8: Team analysis
        step_data = {
            "step": 8,
            "_title": "TODO",
            "team_size": random.randint(10, 200),
            "key_executives": random.randint(3, 8),
            "technical_ratio": f"{random.randint(40, 80)}%"
        }
        jobs[job_id].status = "Analyzing team composition..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 9: Technology stack
        step_data = {
            "step": 9,
            "_title": "TODO",
            "tech_stack_count": random.randint(5, 15),
            "main_languages": random.randint(3, 8),
            "infrastructure": random.choice(["AWS", "GCP", "Azure", "Hybrid"])
        }
        jobs[job_id].status = "Evaluating technology stack..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 10: Growth metrics
        step_data = {
            "step": 10,
            "_title": "TODO",
            "user_growth": f"{random.randint(10, 100)}%",
            "mrr_growth": f"{random.randint(5, 50)}%",
            "retention": f"{random.randint(70, 95)}%"
        }
        jobs[job_id].status = "Calculating growth metrics..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 11: Risk assessment
        step_data = {
            "step": 11,
            "_title": "TODO",
            "risk_score": random.randint(1, 100),
            "key_risks": random.randint(2, 5),
            "mitigation_strategies": random.randint(3, 6)
        }
        jobs[job_id].status = "Performing risk assessment..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 12: Market sentiment
        step_data = {
            "step": 12,
            "_title": "TODO",
            "sentiment_score": random.randint(1, 100),
            "news_mentions": random.randint(10, 1000),
            "social_reach": f"{random.randint(1000, 999999)}+"
        }
        jobs[job_id].status = "Analyzing market sentiment..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 13: Competitive analysis
        step_data = {
            "step": 13,
            "market_position": random.choice(["Leader", "Challenger", "Follower", "Niche Player"]),
            "competitive_advantages": random.randint(2, 5),
            "market_share": f"{random.randint(1, 30)}%"
        }
        jobs[job_id].status = "Evaluating competitive position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 14: Final scoring
        potential_levels = ["Very High", "High", "Medium", "Low"]
        market_sizes = ["$100M+", "$500M+", "$1B+", "$10B+"]
        
        step_data = {
            "step": 14,
            "_title": "TODO",
            "final_score": random.randint(60, 100),
            "investment_recommendation": random.choice(["Strong Buy", "Buy", "Hold", "Watch"])
        }
        jobs[job_id].status = "Generating final report..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Set final result
        jobs[job_id].result = {
            "domain": domain,
            "analyzed_at": datetime.now().isoformat(),
            "metrics": {
                "score": jobs[job_id].current_step_data["final_score"],
                "potential": random.choice(potential_levels),
                "market_size": random.choice(market_sizes),
                "company_age": jobs[job_id].step_history[0]["company_age"],
                "market_position": jobs[job_id].step_history[12]["market_position"],
                "recommendation": jobs[job_id].current_step_data["investment_recommendation"]
            }
        }
        jobs[job_id].completed = True
    except Exception as e:
        jobs[job_id].status = f"Error: {str(e)}"
        jobs[job_id].completed = True
        raise e


@app.post("/summarize-step")
async def summarize_step(request: StepSummaryRequest):
    # Format the step data into readable text
    formatted_text = format_step_data(request.step_data)
    summary = await get_gpt_summary(formatted_text, OPENAI_API_KEY)
    return {"summary": summary}


@app.get("/")
async def root():
    return {"message": "Welcome to Data Driven VC API"}


@app.post("/analyze-domain", response_model=JobResponse)
async def analyze_domain(request: DomainRequest):
    job_id = str(uuid.uuid4())
    jobs[job_id] = JobStatus(status="Initializing analysis...")
    # Start background task
    asyncio.create_task(process_domain(request.domain, job_id))
    return JobResponse(job_id=job_id)


@app.get("/job/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return jobs[job_id]
