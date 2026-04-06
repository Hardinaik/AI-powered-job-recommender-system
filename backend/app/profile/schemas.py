import re
from pydantic import BaseModel, EmailStr, field_validator, model_validator, HttpUrl
from typing import Optional, List
from pydantic_core import PydanticCustomError


class IdNamePair(BaseModel):
    id: int
    name: str

class JobSeekerProfileSchema(BaseModel):
    experience: int = 0
    preferred_domain: Optional[IdNamePair] = None
    preferred_locations: List[IdNamePair] = []

class RecruiterProfileSchema(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    description: Optional[str] = None

class UserProfileResponse(BaseModel):
    fullname: str
    email: EmailStr
    user_role: str
    phone: Optional[str] = None 
    jobseeker_details: Optional[JobSeekerProfileSchema] = None
    recruiter_details: Optional[RecruiterProfileSchema] = None

    class Config:
        from_attributes = True


class PersonalInfoUpdate(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_e164_phone(cls, v: Optional[str]):
        if v is None:
            return v
        v = re.sub(r"[\s\-\.]", "", v)
        e164_regex = r"^\+[1-9]\d{6,14}$"
        if not re.match(e164_regex, v):
            raise ValueError(
                "Invalid E.164 phone format. Must start with '+' followed by 7-15 digits. "
                "The first digit of the country code cannot be 0. Example: +919876543210"
            )
        return v
    
class JobSeekerPrefUpdate(BaseModel):
    experience: Optional[int] = None
    preferred_domain_id: Optional[int] = None
    location_ids: Optional[List[int]] = None


class CompanyInfoUpdate(BaseModel):
    company_name: Optional[str] = None
    website: Optional[str] = None
    linkedin: Optional[str] = None
    description: Optional[str] = None

    @field_validator("website")
    @classmethod
    def validate_website(cls, v: Optional[str]):
        if v is None:
            return v
        HttpUrl(v)
        return str(v)

    @field_validator("linkedin")                       
    @classmethod
    def validate_linkedin(cls, v: Optional[str]):
        if v is None:
            return v
        pattern = r'^https?://(www\.)?linkedin\.com/(in|company)/[\w\-]+/?$'
        if not re.match(pattern, v):
            raise ValueError(
                "Invalid LinkedIn URL. Expected format: "
                "https://www.linkedin.com/in/username or "
                "https://www.linkedin.com/company/name"
            )
        return str(v)


class PasswordChange(BaseModel):
    current_pass: str
    new_pass: str
    confirm_pass: str

    @field_validator("new_pass")
    @classmethod
    def validate_new_password(cls, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'
        if not re.match(pattern, value):
            raise PydanticCustomError(
                "password_error",
                "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character."
            )
        return value

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.new_pass != self.confirm_pass:
            raise ValueError("Confirm password must match new password")
        if self.current_pass == self.new_pass:
            raise ValueError("New password cannot be same as current password")
        return self