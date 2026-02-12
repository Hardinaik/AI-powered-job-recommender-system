from fastapi import APIRouter, Depends, HTTPException
from app.utils import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/jobseeker")
def jobseeker_dashboard(current_user: dict = Depends(get_current_user)):

    if current_user["role"] != "jobseeker":
        raise HTTPException(status_code=403, detail="Access denied")

    return {"message": "Welcome Jobseeker"}


@router.get("/recruiter")
def recruiter_dashboard(current_user: dict = Depends(get_current_user)):

    if current_user["role"] != "recruiter":
        raise HTTPException(status_code=403, detail="Access denied")

    return {"message": "Welcome Recruiter"}
