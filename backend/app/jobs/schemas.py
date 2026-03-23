import re
from pydantic import BaseModel
from typing import List
from uuid import UUID



class JobPostRequest(BaseModel):
    job_title: str
    company_name: str
    industry_domain_id: int
    location_ids: List[int]
    min_experience: int
    job_description: str


class JobPostResponse(BaseModel):
    job_id: UUID
    job_title: str
    company_name: str

    class Config:
        from_attributes = True

class JobResponse(BaseModel):
    job_id: UUID
    job_title: str
    locations: List[str]
    job_description: str
    min_experience: int
    company_name:str
    
    class Config:
        from_attributes = True


class DeleteJobResponse(BaseModel):
    job_id:UUID