import re
from pydantic import BaseModel, EmailStr,field_validator,Field
from typing import Literal,List
from uuid import UUID
from datetime import datetime
from pydantic_core import PydanticCustomError

class SignupRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    user_role: Literal["jobseeker", "recruiter"]
    @field_validator("password")
    def validate_password(cls, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

        if not re.match(pattern, value):
            raise PydanticCustomError(
                "password_error",
                "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character."
            )
        return value



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

class SaveJobResponse(BaseModel):
    job_id:UUID
    message: str

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


    






