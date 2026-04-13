from pydantic import BaseModel
from typing import Optional


class ApplicationNotifyForm(BaseModel):
    """
    Submitted by the frontend when the user clicks Send / Confirm on the apply form.
    All fields arrive from the form — frontend pre-fills them via GET /prefill,
    but every field is editable by the user before submission.
    """
    name:           str           # pre-filled: users.fullname
    email:          str           # pre-filled: users.email
    phone:          Optional[str] = None  # pre-filled: users.phone (optional in DB)
    experience:     int           = 0    # pre-filled: jobseeker_profile.experience (optional in DB)
    resume_url:     Optional[str] = None  # pre-filled: resume.resume_url (optional in DB)
    linkedin:       Optional[str] = None  # form only — no DB source
    why_interested: str                   # form only — required


class ApplicationPrefillResponse(BaseModel):
    """
    Returned by GET /prefill.
    Frontend uses these values to populate the apply form fields.
    All optional fields may be None — frontend must handle empty state.
    """
    name:       str
    email:      str
    phone:      Optional[str] = None
    experience: int           = 0
    resume_url: Optional[str] = None