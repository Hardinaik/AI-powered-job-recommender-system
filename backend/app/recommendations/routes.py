from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from app.database import get_db
from app.models import Job, Location, IndustryDomain
from app.schemas import JobResponse

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/jobs", response_model=List[JobResponse])
def get_jobs(
    domain_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    experience: Optional[int] = Query(None),
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    # 1. Base Query with Eager Loading (prevents extra DB hits for locations)
    query = db.query(Job).options(joinedload(Job.locations))

    # 2. Apply Optional Filters (The Sieve Logic)
    if domain_id:
        query = query.filter(Job.industry_domain_id == domain_id)

    if location_id:
        # Filter through the Many-to-Many relationship using the Location ID
        query = query.join(Job.locations).filter(Location.id == location_id)

    if experience is not None:
        # Show jobs where the required experience is less than or equal to user input
        query = query.filter(Job.min_experience <= experience)

    # 3. Execution with Pagination
    jobs = (
        query.order_by(Job.posted_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    # 4. Manual mapping to the Response Schema
    return [
        JobResponse(
            job_id=job.job_id,
            job_title=job.job_title,
            locations=[loc.name for loc in job.locations],
            job_description=job.job_description,
            min_experience=job.min_experience,
            company_name=job.company_name
        )
        for job in jobs
    ]