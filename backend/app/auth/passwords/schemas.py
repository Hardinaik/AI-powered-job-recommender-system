import re
from pydantic import BaseModel, EmailStr,field_validator
from pydantic_core import PydanticCustomError


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator("new_password")
    def validate_password(cls, value):
        pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&]).{8,}$'

        if not re.match(pattern, value):
            raise PydanticCustomError(
                "password_error",
                "Password must be at least 8 characters long and include uppercase, lowercase, number, and special character."
            )
        return value
