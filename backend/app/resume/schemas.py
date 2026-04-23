from pydantic import BaseModel, field_validator

class ResumeExtraction(BaseModel):
    skills: str
    work_experience: list[str] = []
    projects: list[str] = []

    @field_validator("skills")
    @classmethod
    def skills_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("skills cannot be empty")
        return v.strip()

    @field_validator("work_experience", "projects", mode="before")
    @classmethod
    def coerce_to_list(cls, v) -> list:
        # Guard against LLM returning a string instead of a list
        if not isinstance(v, list):
            return []
        return v
