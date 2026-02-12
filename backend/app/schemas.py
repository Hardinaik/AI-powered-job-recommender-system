from pydantic import BaseModel, EmailStr
from typing import Literal
from uuid import UUID

class SignupRequest(BaseModel):
    fullname: str
    email: EmailStr
    password: str
    user_role: Literal["jobseeker", "recruiter"]

class UserResponse(BaseModel):
    user_id: UUID
    fullname: str
    email: EmailStr
    user_role: str

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email:EmailStr
    password:str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str