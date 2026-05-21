from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID


# ─── Common building blocks ───────────────────────────────────────────────────

class IdNamePair(BaseModel):
    id: int
    name: str


# ─── Job ─────────────────────────────────────────────────────────────────────

class JobItem(BaseModel):
    
    job_id: UUID
    job_title: str
    locations: List[str]
    job_description: str
    min_experience: int
    max_experience: int
    company_name: str
    match_score: float = Field(default=0.0)

    class Config:
        from_attributes = True


class PaginatedJobResponse(BaseModel):
    
    total: int
    skip: int
    limit: int
    jobs: List[JobItem]


# ─── Company ─────────────────────────────────────────────────────────────────

class CompanyDetails(BaseModel):
   
    company_name: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    description: Optional[str] = None