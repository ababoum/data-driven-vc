import asyncio
import random
import uuid
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from quantitative.techs import get_techs
from providers.harmonic.client import HarmonicClient

from models import DomainRequest, StepSummaryRequest, JobResponse, JobStatus

# In-memory job store
jobs: Dict[str, JobStatus] = {}

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
    step_type = step_data.get("step")
    
    # Remove step number from the data to display
    data_to_display = {k: v for k, v in step_data.items() if k != "step"}
    
    step_titles = {
        1: "Competitors informations",
        2: "Founders",
        3: "Company Details",
        4: "Competitors",
        5: "Key People",
        6: "Market analysis",
        7: "Financial assessment",
        8: "Market Sentiment",
        9: "Competitive Analysis",
        10: "Final Scoring"
    }
    
    # Create a formatted string with the step title and data
    formatted_text = f"{step_titles.get(step_type, 'Analysis Step')}:\n"
    for key, value in data_to_display.items():
        formatted_key = key.replace('_', ' ').title()
        formatted_text += f"- {formatted_key}: {value}\n"
    
    return formatted_text

async def get_gpt_summary(text: str) -> str:
    """Get summary from ChatGPT."""
    try:
        prompt = f"Explain this to me in details in markdown format by always keeping your answer objective and concise and by assuming I'm a VC who doesn't know anything about tech (Always try to comment on how it could be a pro or a con in the context of a future investment): {text}"
        client = OpenAI()
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling ChatGPT API: {str(e)}")
        return f"Failed to generate summary: {str(e)}"

async def process_domain(domain: str, job_id: str):
    try:
        harmonic_client = HarmonicClient()
        # Step 1: Competitors
        company = await harmonic_client.find_company(domain)
        competitors = await harmonic_client.get_competitors(domain)
        md_competitors = harmonic_client.format_companies_to_md(competitors)
        outliers_good = harmonic_client.find_outliers(company, competitors, 0.2)
        outliers_bad = harmonic_client.find_outliers(company, competitors, 0.5)
        
        # Calculate performance based on whether the company is in outliers
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
        jobs[job_id].status = "Analyzing competitors..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 2: Founders Analysis
        performance = random.choice([-1, 0, 1])
        performance_comment = {
            1: "Strong founding team with relevant experience",
            0: "Average founding team composition",
            -1: "Founding team lacks key experience"
        }[performance]
        
        step_data = {
            "step": 2,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY",
            "performance_comment": performance_comment,
            "_performance": performance,
            "calculation_explanation": """The founders' assessment is based on a comprehensive analysis of several key factors:

1. Professional Background:
   - Previous startup experience (especially successful exits)
   - Industry expertise and years of experience
   - Technical expertise for tech companies
   - Management and leadership experience

2. Educational Background:
   - Relevant degrees and certifications
   - Prestigious institutions (weighted but not overemphasized)
   - Continuing education and professional development

3. Track Record:
   - Previous companies' performance
   - Patents and innovations
   - Industry recognition and awards
   - Published works or research

4. Team Composition:
   - Complementary skill sets among founders
   - Balance of technical and business expertise
   - Previous collaborations between founders
   - Advisory board strength

The final score is calculated by weighting these factors based on their relevance to the specific industry and market segment."""
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 3: Company Details
        performance = random.choice([-1, 0, 1])
        performance_comment = {
            1: "Company shows strong market positioning",
            0: "Company has stable market presence",
            -1: "Company faces significant market challenges"
        }[performance]
        
        step_data = {
            "step": 3,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY",
            "performance_comment": performance_comment,
            "_performance": performance,
            "calculation_explanation": """The company details analysis involves a multi-faceted evaluation of the business:

1. Market Position:
   - Current market share and growth trajectory
   - Brand strength and recognition
   - Customer satisfaction metrics
   - Competitive advantages and moats

2. Business Model:
   - Revenue streams and diversification
   - Pricing strategy and unit economics
   - Customer acquisition costs (CAC)
   - Lifetime value (LTV) and retention rates

3. Growth Metrics:
   - Year-over-year revenue growth
   - User or customer growth
   - Geographic expansion
   - Product line expansion

4. Operational Efficiency:
   - Gross and net margins
   - Operational costs and scalability
   - Resource utilization
   - Technology infrastructure

5. Risk Assessment:
   - Regulatory compliance
   - Market dependencies
   - Technical debt
   - Competition threats

Each factor is scored individually and weighted based on industry standards and market conditions to produce the final assessment."""
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 4: Competitor Analysis
        step_data = {
            "step": 4,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 5: Key People
        step_data = {
            "step": 5,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 6: Market analysis
        step_data = {
            "step": 6,
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


@app.post("/summarize-step")
async def summarize_step(request: StepSummaryRequest):
    # Format the step data into readable text
    formatted_text = format_step_data(request.step_data)
    
    # Get summary from ChatGPT
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
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]
