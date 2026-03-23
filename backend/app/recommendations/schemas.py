
from pydantic import BaseModel,Field
from typing import List
from uuid import UUID



class RecJobResponse(BaseModel):
    job_id: UUID
    job_title: str
    locations: List[str]
    job_description: str
    min_experience: int
    company_name:str
    match_score:float = Field(..., description="The AI-calculated similarity score (0-100)")

    class Config:
        from_attributes = True