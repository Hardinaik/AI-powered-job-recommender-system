from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import User, JobSeekerProfile,RecruiterProfile,Location
from .schemas import UserProfileResponse,PersonalInfoUpdate,CompanyInfoUpdate,JobSeekerPrefUpdate
from .utils import get_current_user_obj

router=APIRouter(prefix="/profile",tags=["Profile"])


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import User, JobSeekerProfile, RecruiterProfile
from .schemas import UserProfileResponse, PersonalInfoUpdate
from .utils import get_current_user_obj

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("/details", response_model=UserProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    user_obj: User = Depends(get_current_user_obj)
):
    # 1. Fetch user with all relationships
    user = db.query(User).options(
        joinedload(User.jobseeker_profile).joinedload(JobSeekerProfile.preferred_domain),
        joinedload(User.preferred_locations),
        joinedload(User.recruiter_profile)  
    ).filter(User.user_id == user_obj.user_id).first()

    # 2. Base Data (Phone is directly on 'user')
    result = {
        "fullname": user.fullname,
        "email": user.email,
        "user_role": user.user_role,
        "phone": user.phone, 
        "jobseeker_details": None,
        "recruiter_details": None
    }

    # 3. Role-Specific Logic
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
            "description": profile.description if profile else None
        }

    return result


@router.patch("/personal")
def update_personal_info(
    payload: PersonalInfoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_obj)
):
    # 1. Update User table directly
    if payload.fullname is not None:
        user.fullname = payload.fullname
    
    if payload.phone is not None:
        user.phone = payload.phone

    try:
        db.commit()
        return {"message": "Personal information updated successfully"}
    except IntegrityError:
        db.rollback()
        # This handles the 'UNIQUE' constraint on the phone column
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
    # 1. Role Security
    if user.user_role != "jobseeker":
        raise HTTPException(
            status_code=403, 
            detail="Only jobseekers can update job preferences."
        )

    try:
        # 2. Update JobSeekerProfile table (Upsert logic)
        profile = user.jobseeker_profile
        if not profile:
            profile = JobSeekerProfile(user_id=user.user_id)
            db.add(profile)

        if payload.experience is not None:
            profile.experience = payload.experience
        
        if payload.preferred_domain_id is not None:
            profile.preferred_domain_id = payload.preferred_domain_id

        # 3. Sync Many-to-Many Locations
        if payload.location_ids is not None:
            # Fetch the actual Location objects from the database for the given IDs
            new_locations = db.query(Location).filter(Location.id.in_(payload.location_ids)).all()
            
            # SQLAlchemy handles the junction table (jobseeker_preferred_locations)
            # automatically. Setting the list replaces all old entries with new ones.
            user.preferred_locations = new_locations

        db.commit()
        return {"message": "Job preferences updated successfully"}

    except Exception as e:
        db.rollback()
        # Log the error 'e' here for debugging
        raise HTTPException(status_code=500, detail="Failed to update preferences")
    

@router.patch("/company")
def update_company_details(
    payload: CompanyInfoUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_obj)
):
    # 1. Role Authorization
    if user.user_role != "recruiter":
        raise HTTPException(
            status_code=403, 
            detail="Access denied. Only recruiters can update company information."
        )

    try:
        # 2. Fetch existing profile or initialize a new one (Upsert)
        profile = user.recruiter_profile
        if not profile:
            profile = RecruiterProfile(user_id=user.user_id)
            db.add(profile)

        # 3. Apply updates for provided fields
        if payload.company_name is not None:
            profile.company_name = payload.company_name
            
        if payload.website is not None:
            profile.website = payload.website
            
        if payload.description is not None:
            profile.description = payload.description

        # 4. Save to Database
        db.commit()
        return {"message": "Company details updated successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="An error occurred while updating company details.")