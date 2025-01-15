from typing import Optional, List
from pydantic import BaseModel


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
