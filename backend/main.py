from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import uuid
import random
import requests
from typing import Dict, Optional, List
from datetime import datetime
from openai import OpenAI

class DomainRequest(BaseModel):
    domain: str

class StepSummaryRequest(BaseModel):
    step_data: dict

class JobResponse(BaseModel):
    job_id: str

class JobStatus(BaseModel):
    status: str
    result: Optional[dict] = None
    completed: bool = False
    current_step_data: Optional[dict] = None
    step_history: List[dict] = []

# Initialize OpenAI client
client = OpenAI(api_key="")

# In-memory job store
jobs: Dict[str, JobStatus] = {}

app = FastAPI(title="Data Driven VC API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
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
        1: "Company Informations",
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
        prompt = f"Explain this to me in details in .md format by always keeping your answer objective and concise and by assuming I'm a VC who doesn't know anything about tech (Always try to comment on how it could be a pro or a con in the context of a future investment): {text}"
        
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling ChatGPT API: {str(e)}")
        return f"Failed to generate summary: {str(e)}"

async def process_domain(domain: str, job_id: str):
    try:
        # Step 1: Company Enrichment
        step_data = {
            "step": 1,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 2: Founders Analysis
        step_data = {
            "step": 2,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
        }
        jobs[job_id].status = "Analyzing market position..."
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        await asyncio.sleep(1)

        # Step 3: Company Details
        step_data = {
            "step": 3,
            "market_size": f"${random.randint(1, 100)}B",
            "competitors": random.randint(5, 20),
            "market_growth": f"{random.randint(5, 30)}% YoY"
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