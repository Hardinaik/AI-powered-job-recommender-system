import re
from pydantic import BaseModel, EmailStr,field_validator
from typing import Literal
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
