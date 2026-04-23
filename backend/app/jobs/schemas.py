import re
from pydantic import BaseModel,field_validator
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

class JobExtraction(BaseModel):
    job_role: str = ""
    skills: str
    job_summary: str

    @field_validator("skills", "job_summary")
    @classmethod
    def must_not_be_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} cannot be empty")
        return v.strip()