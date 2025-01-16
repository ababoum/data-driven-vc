import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

from providers.harmonic.client import HarmonicClient
from qualitative.founders import qualify_founder

from models import DomainRequest, StepSummaryRequest, JobResponse, JobStatus
from utils import get_gpt_summary
from workflow import WebsiteAnalysisWorkflow

# In-memory job store
jobs: Dict[str, JobStatus] = {}


load_dotenv("../.env", override=True)
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


async def process_domain(domain: str, job_id: str):
    try:
        workflow = WebsiteAnalysisWorkflow(domain)
        # Step 1: Competitors
        jobs[job_id].status = "Analyzing competitors..."
        step_data = await workflow.generate_competitors_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        # Step 2: GitHub Analysis
        jobs[job_id].status = "Analyzing GitHub..."
        step_data = await workflow.generate_github_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        # Step 3: Code Quality
        jobs[job_id].status = "Analyzing code quality..."
        step_data = await workflow.generate_code_quality_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        # Step 4: Founder Analysis
        harmonic_client = HarmonicClient()
        company = await harmonic_client.find_company(domain)
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
    summary = await get_gpt_summary(formatted_text)
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
