import asyncio
import uuid
from typing import Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette import status

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
        # Step 0: Tech Trends
        jobs[job_id].status = "Analyzing tech trends..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_tech_summary_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        
        # Step 1: Founder Analysis
        jobs[job_id].status = "Analyzing founders..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_founders_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        
        # Step 2: GitHub Analysis
        jobs[job_id].status = "Analyzing GitHub..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_github_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        # Step 3: Code Quality
        jobs[job_id].status = "Analyzing code quality..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_code_quality_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        # Step 4: Competitors
        jobs[job_id].status = "Analyzing competitors..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_competitors_report()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)
        
        # Step 5: Memo
        jobs[job_id].status = "Generating memo..."
        # await asyncio.sleep(1.0)
        step_data = await workflow.generate_memo()
        jobs[job_id].current_step_data = step_data
        jobs[job_id].step_history.append(step_data)

        jobs[job_id].status = "Analysis complete!"
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
