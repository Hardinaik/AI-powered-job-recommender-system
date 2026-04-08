from sqlalchemy import (
    Column, Text, Integer, String, Boolean,TIMESTAMP,
    ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.database import Base


# ================= USERS =================
class User(Base):
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "user_role IN ('jobseeker', 'recruiter')",
            name="users_user_role_check"
        ),
    )

    user_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    fullname = Column(Text, nullable=False)
    email = Column(Text, unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    phone = Column(Text, unique=True, nullable=True)
    user_role = Column(Text, nullable=False)
    profile_image_path=Column(Text,unique=True)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    # Relationships
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete")

    jobseeker_profile = relationship(
        "JobSeekerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )

    recruiter_profile = relationship(
        "RecruiterProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete"
    )

    preferred_locations = relationship(
        "Location",
        secondary="jobseeker_preferred_locations",
        back_populates="users"
    )

    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete")
    applications = relationship("Application", back_populates="job_seeker", cascade="all, delete")
    savedjobs = relationship("SavedJob", back_populates="job_seeker", cascade="all, delete")


# ================= RESUME =================
class Resume(Base):
    __tablename__ = "resume"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)

    resume_url = Column(Text,unique=True)
    resume_text=Column(Text,nullable=False)
    work_embedding = Column(Vector(384))
    skill_embedding = Column(Vector(384), nullable=False)
    project_embedding=Column(Vector(384))

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User", back_populates="resume")


# ================= INDUSTRY DOMAIN =================
class IndustryDomain(Base):
    __tablename__ = "industrydomains"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship("Job", back_populates="industry")


# ================= LOCATION =================
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship(
        "Job",
        secondary="job_locations",
        back_populates="locations"
    )

    users = relationship(
        "User",
        secondary="jobseeker_preferred_locations",
        back_populates="preferred_locations"
    )


# ================= JOB =================
class Job(Base):
    __tablename__ = "job"

    job_id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())

    job_title = Column(Text, nullable=False)
    company_name = Column(String(100))

    industry_domain_id = Column(Integer, ForeignKey("industrydomains.id"))

    job_description = Column(Text, nullable=False)
    min_experience = Column(Integer, default=0)

    recruiter_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))

    job_embedding = Column(Vector(384), nullable=False)
    skill_embedding = Column(Vector(384), nullable=False)

    posted_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    recruiter = relationship("User", back_populates="jobs")
    industry = relationship("IndustryDomain", back_populates="jobs")

    applications = relationship("Application", back_populates="job", cascade="all, delete")
    savedjobs = relationship("SavedJob", back_populates="job", cascade="all, delete")

    locations = relationship(
        "Location",
        secondary="job_locations",
        back_populates="jobs"
    )


# ================= APPLICATION =================
class Application(Base):
    __tablename__ = "applications"

    job_seeker_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job.job_id", ondelete="CASCADE"), primary_key=True)

    applied_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    job_seeker = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")


# ================= SAVED JOB =================
class SavedJob(Base):
    __tablename__ = "savedjobs"

    job_seeker_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    job_id = Column(UUID(as_uuid=True), ForeignKey("job.job_id", ondelete="CASCADE"), primary_key=True)

    saved_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    job_seeker = relationship("User", back_populates="savedjobs")
    job = relationship("Job", back_populates="savedjobs")


# ================= JOB LOCATION =================
class JobLocation(Base):
    __tablename__ = "job_locations"

    job_id = Column(UUID(as_uuid=True), ForeignKey("job.job_id", ondelete="CASCADE"), primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True)


# ================= JOBSEEKER PROFILE =================
class JobSeekerProfile(Base):
    __tablename__ = "jobseeker_profile"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)

    
    experience = Column(Integer, default=0)
    preferred_domain_id = Column(Integer, ForeignKey("industrydomains.id"))

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User", back_populates="jobseeker_profile")
    preferred_domain = relationship("IndustryDomain")


# ================= RECRUITER PROFILE =================
class RecruiterProfile(Base):
    __tablename__ = "recruiter_profile"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)

    
    company_name = Column(Text)
    website = Column(Text)
    linkedin=Column(Text)
    description = Column(Text)

    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User", back_populates="recruiter_profile")


# ================= JOBSEEKER PREFERRED LOCATIONS =================
class JobSeekerPreferredLocation(Base):
    __tablename__ = "jobseeker_preferred_locations"

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    location_id = Column(Integer, ForeignKey("locations.id", ondelete="CASCADE"), primary_key=True)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    # Use UUID to match your User table style
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    
    # Link to your User table using the correct ID column name
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    
    # Store the HASH of the token, not the token itself
    token_hash = Column(Text, unique=True, nullable=False)
    
    # Timing logic
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    
    # Status
    used = Column(Boolean, default=False)

    # Relationship (Optional, but helpful)
    user = relationship("User")