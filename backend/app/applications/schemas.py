
from pydantic import BaseModel
from typing import List
from uuid import UUID


class SaveJobResponse(BaseModel):
    job_id:UUID
    message: str


class JobResponse(BaseModel):
    job_id: UUID
    job_title: str
    locations: List[str]
    job_description: str
    min_experience: int
    company_name:str
    
    class Config:
        from_attributes = True