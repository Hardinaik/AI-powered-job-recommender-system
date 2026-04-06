from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from sqlalchemy.exc import IntegrityError
from app.models import User, JobSeekerProfile,RecruiterProfile,Location
from .schemas import UserProfileResponse,PersonalInfoUpdate,CompanyInfoUpdate,JobSeekerPrefUpdate,PasswordChange
from .utils import get_current_user_obj
from app.utils import verify_password,hash_password


router=APIRouter(prefix="/profile",tags=["Profile"])

@router.get("/details", response_model=UserProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    user_obj: User = Depends(get_current_user_obj)
):
    user = db.query(User).options(
        joinedload(User.jobseeker_profile).joinedload(JobSeekerProfile.preferred_domain),
        joinedload(User.preferred_locations),
        joinedload(User.recruiter_profile)  
    ).filter(User.user_id == user_obj.user_id).first()

    result = {
        "fullname": user.fullname,
        "email": user.email,
        "user_role": user.user_role,
        "phone": user.phone, 
        "jobseeker_details": None,
        "recruiter_details": None
    }

    if user.user_role == "jobseeker":
        profile = user.jobseeker_profile
        result["jobseeker_details"] = {
            "experience": profile.experience if profile else 0,
            "preferred_domain": {
                "id": profile.preferred_domain.id, 
                "name": profile.preferred_domain.name
            } if (profile and profile.preferred_domain) else None,
            "preferred_locations": [
                {"id": loc.id, "name": loc.name} for loc in user.preferred_locations
            ]
        }
    elif user.user_role == "recruiter":
        profile = user.recruiter_profile
        result["recruiter_details"] = {
            "company_name": profile.company_name if profile else None,
            "website": profile.website if profile else None,
            "linkedin": profile.linkedin if profile else None,
            "description": profile.description if profile else None
        }

    return result


@router.patch("/personal")
def update_personal_info(
    payload: PersonalInfoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_obj)
):
    if payload.fullname is not None:
        user.fullname = payload.fullname
    
    if payload.phone is not None:
        user.phone = payload.phone

    try:
        db.commit()
        return {"message": "Personal information updated successfully"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="This phone number is already in use by another account."
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")


@router.patch("/preferences")
def update_job_preferences(
    payload: JobSeekerPrefUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_obj)
):
    if user.user_role != "jobseeker":
        raise HTTPException(
            status_code=403, 
            detail="Only jobseekers can update job preferences."
        )

    try:
        profile = user.jobseeker_profile
        if not profile:
            profile = JobSeekerProfile(user_id=user.user_id)
            db.add(profile)

        if payload.experience is not None:
            profile.experience = payload.experience
        
        if payload.preferred_domain_id is not None:
            profile.preferred_domain_id = payload.preferred_domain_id

        if payload.location_ids is not None:
            new_locations = db.query(Location).filter(Location.id.in_(payload.location_ids)).all()
            user.preferred_locations = new_locations

        db.commit()
        return {"message": "Job preferences updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update preferences")
    

@router.patch("/company")
def update_company_details(
    payload: CompanyInfoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_obj)
):
    if user.user_role != "recruiter":
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only recruiters can update company information."
        )

    try:
        profile = user.recruiter_profile
        if not profile:
            profile = RecruiterProfile(user_id=user.user_id)
            db.add(profile)

        if payload.company_name is not None:
            profile.company_name = payload.company_name
            
        if payload.website is not None:
            profile.website = payload.website

        if payload.linkedin is not None:       
            profile.linkedin = payload.linkedin  
            
        if payload.description is not None:
            profile.description = payload.description

        db.commit()
        return {"message": "Company details updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while updating company details.")
    

@router.patch("/change-password")
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_obj)
):
    if not verify_password(payload.current_pass, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    current_user.password_hash = hash_password(payload.new_pass)
    db.commit()
    db.refresh(current_user)

    return {"message": "Password updated successfully"}


