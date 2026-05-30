from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from app.limiter import limiter
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, timezone
from app.exceptions import LLMError, EmbeddingError
from .schemas import JobPostRequest, JobPostResponse, DeleteJobResponse
from app.schemas import JobItem, PaginatedJobResponse
from app.database import get_db
from app.models import Job, Location, IndustryDomain
from .utils import create_job_embedding, detect_job_level
from app.utils import get_current_recruiter, get_current_user, get_current_jobseeker, _tokenize
from typing import List
from uuid import UUID


router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.get("/locations")
def get_locations(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return db.query(Location).all()


@router.get("/industry-domains")
def get_industry_domains(db: Session = Depends(get_db), _: dict = Depends(get_current_user)):
    return db.query(IndustryDomain).all()


@router.post("/post", response_model=JobPostResponse)
@limiter.limit("2/minute")
def create_job(
    request: Request,
    job: JobPostRequest,
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    domain = db.query(IndustryDomain).filter(
        IndustryDomain.id == job.industry_domain_id
    ).first()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid industry_domain_id"
        )

    locations = db.query(Location).filter(
        Location.id.in_(job.location_ids)
    ).all()

    if len(locations) != len(job.location_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more location_ids are invalid"
        )

    try:
        skill_embedding, job_embedding = create_job_embedding(job.job_description)
    except LLMError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except EmbeddingError as e:
        raise HTTPException(status_code=503, detail=str(e))

    new_job = Job(
        job_title          = job.job_title,
        company_name       = job.company_name,
        industry_domain_id = job.industry_domain_id,
        min_experience     = job.min_experience,
        max_experience     = job.max_experience,
        job_level          = detect_job_level(job.min_experience, job.max_experience),
        job_description    = job.job_description,
        recruiter_id       = current_recruiter["user_id"],
        skill_embedding    = skill_embedding,
        job_embedding      = job_embedding,
        bm25_tokens        = _tokenize(job.job_description),
        posted_at          = datetime.now(timezone.utc)
    )

    new_job.locations = locations
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/postedjobs", response_model=List[JobItem])
def get_posted_jobs(
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    jobs = (
        db.query(Job)
        .options(joinedload(Job.locations))
        .filter(Job.recruiter_id == current_recruiter["user_id"])
        .order_by(Job.posted_at.desc())
        .all()
    )

    return [
        JobItem(
            job_id          = job.job_id,
            job_title       = job.job_title,
            company_name    = job.company_name,
            locations       = [loc.name for loc in job.locations],
            job_description = job.job_description,
            min_experience  = job.min_experience,
            max_experience  = job.max_experience,
            match_score     = 0.0,
        )
        for job in jobs
    ]


@router.delete("/{job_id}", response_model=DeleteJobResponse)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):
    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.recruiter_id == current_recruiter["user_id"]
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    db.delete(job)
    db.commit()

    return DeleteJobResponse(job_id=job_id)


@router.get("/all", response_model=PaginatedJobResponse)
async def get_all_jobs(
    skip: int          = Query(default=0, ge=0),
    limit: int         = Query(default=10, ge=1, le=100),
    db: Session        = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    base_query = db.query(Job).order_by(Job.posted_at.desc())

    total = base_query.count()

    jobs = (
        base_query
        .options(joinedload(Job.locations))
        .offset(skip)
        .limit(limit)
        .all()
    )

    return PaginatedJobResponse(
        total = total,
        skip  = skip,
        limit = limit,
        jobs  = [
            JobItem(
                job_id          = job.job_id,
                job_title       = job.job_title,
                locations       = [loc.name for loc in job.locations],
                job_description = job.job_description,
                min_experience  = job.min_experience,
                max_experience  = job.max_experience,
                company_name    = job.company_name,
                match_score     = 0.0,
            )
            for job in jobs
        ]
    )