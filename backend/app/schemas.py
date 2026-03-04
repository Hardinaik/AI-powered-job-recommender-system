from pydantic import BaseModel, EmailStr
from typing import Literal,List
from uuid import UUID
from datetime import datetime


class SignupRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    user_role: Literal["jobseeker", "recruiter"]

class LoginRequest(BaseModel):
    email:EmailStr
    password:str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str


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
    min_experience: int

    class Config:
        from_attributes = True

class PostedJobResponse(BaseModel):
    job_id: UUID
    job_title: str
    locations: List[str]
    job_description: str

    
    class Config:
        from_attributes = True




class DeleteJobResponse(BaseModel):
    job_id:UUID

class SaveJobResponse(BaseModel):
    job_id:UUID
    message: str


