from sqlalchemy import (
    Column,
    Text,
    Integer,
    String,
    TIMESTAMP,
    ForeignKey,
    CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base

# USERS
class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "user_role IN ('jobseeker', 'recruiter')",
            name="users_user_role_check"
        ),
    )

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    fullname = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    user_role = Column(Text, nullable=False)

    created_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # Relationships
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete")
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete")
    applications = relationship("Application", back_populates="job_seeker", cascade="all, delete")
    savedjobs = relationship("SavedJob", back_populates="job_seeker", cascade="all, delete")


# RESUME
class Resume(Base):
    __tablename__ = "resume"

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    resume_text = Column(Text, nullable=False)
    resume_embedding = Column(Vector(384), nullable=False)
    skill_embedding = Column(Vector(384), nullable=False)

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    user = relationship("User", back_populates="resume")


# INDUSTRY DOMAINS
class IndustryDomain(Base):
    __tablename__ = "industrydomains"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship("Job", back_populates="industry")


# LOCATIONS

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship(
        "Job",
        secondary="job_locations",
        back_populates="locations"
    )



# JOB
class Job(Base):
    __tablename__ = "job"

    job_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    job_title = Column(Text, nullable=False)
    company_name = Column(String(100))

    industry_domain_id = Column(
        Integer,
        ForeignKey("industrydomains.id")
    )

    job_description = Column(Text, nullable=False)
    min_experience = Column(Integer, default=0)

    recruiter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE")
    )

    job_embedding = Column(Vector(384), nullable=False)
    skill_embedding = Column(Vector(384), nullable=False)

    posted_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # Relationships
    recruiter = relationship("User", back_populates="jobs")
    industry = relationship("IndustryDomain", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete")
    savedjobs = relationship("SavedJob", back_populates="job", cascade="all, delete")

    locations = relationship(
        "Location",
        secondary="job_locations",
        back_populates="jobs"
    )


# APPLICATIONS
class Application(Base):
    __tablename__ = "applications"

    job_seeker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job.job_id", ondelete="CASCADE"),
        primary_key=True
    )

    applied_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    job_seeker = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")



# SAVED JOBS
class SavedJob(Base):
    __tablename__ = "savedjobs"

    job_seeker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job.job_id", ondelete="CASCADE"),
        primary_key=True
    )

    saved_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    job_seeker = relationship("User", back_populates="savedjobs")
    job = relationship("Job", back_populates="savedjobs")



# JOB LOCATIONS (M2M)
class JobLocation(Base):
    __tablename__ = "job_locations"

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("job.job_id", ondelete="CASCADE"),
        primary_key=True
    )

    location_id = Column(
        Integer,
        ForeignKey("locations.id", ondelete="CASCADE"),
        primary_key=True
    )