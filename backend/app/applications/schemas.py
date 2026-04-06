
from pydantic import BaseModel
from typing import List,Optional
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

class ShowCompanyDetails(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    description: Optional[str] = None