import re
from pydantic import BaseModel, EmailStr,field_validator,HttpUrl
from typing import Optional, List

# For Dropdown consistency (ID + Name)
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

import re
from pydantic import BaseModel, field_validator
from typing import Optional

class PersonalInfoUpdate(BaseModel):
    fullname: Optional[str] = None
    phone: Optional[str] = None

    @field_validator("phone")
    @classmethod
    def validate_e164_phone(cls, v: Optional[str]):
        if v is None:
            return v
        
        # 1. Pre-process: Remove common 'noise' characters (spaces, dashes, dots)
        # This makes the API user-friendly
        v = re.sub(r"[\s\-\.]", "", v)

        # 2. Strict E.164 Regex Breakdown:
        # ^\+           -> Must start with '+'
        # [1-9]         -> Country code starts with 1-9 (No leading zero like +01...)
        # \d{6,14}      -> Matches 6 to 14 more digits.
        # Total numeric length: 1 (from [1-9]) + 6 to 14 = 7 to 15 digits.
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
    website: Optional[HttpUrl] = None 
    description: Optional[str] = None