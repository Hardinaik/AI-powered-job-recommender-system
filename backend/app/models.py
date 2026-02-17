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



# USERS TABLE
class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(
            "user_role IN ('jobseeker', 'recruiter')",
            name="user_role_check"
        ),
        {"schema": "public"}
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
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete")
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete")
    applications = relationship("Application", back_populates="job_seeker", cascade="all, delete")



# RESUME TABLE
class Resume(Base):
    __tablename__ = "resume"
    __table_args__ = {"schema": "public"}

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    resume_text = Column(Text, nullable=False)
    resume_embedding = Column(Vector(384), nullable=False)
    skill_embedding = Column(Vector(384), nullable=False)

    updated_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # Relationship
    user = relationship("User", back_populates="resume")



# INDUSTRY DOMAINS TABLE
class IndustryDomain(Base):
    __tablename__ = "industrydomains"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship("Job", back_populates="industry")



# LOCATIONS TABLE
class Location(Base):
    __tablename__ = "locations"
    __table_args__ = {"schema": "public"}

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)

    jobs = relationship("Job", back_populates="location")


# JOB TABLE
class Job(Base):
    __tablename__ = "job"
    __table_args__ = {"schema": "public"}

    job_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )

    job_title = Column(Text, nullable=False)
    company_name = Column(String(100))

    industry_domain_id = Column(
        Integer,
        ForeignKey("public.industrydomains.id")
    )

    location_id = Column(
        Integer,
        ForeignKey("public.locations.id")
    )

    job_description = Column(Text, nullable=False)

    min_experience = Column(Integer, default=0)
    max_experience = Column(Integer, default=0)

    recruiter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.users.user_id", ondelete="CASCADE")
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
    location = relationship("Location", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete")



# APPLICATIONS TABLE
class Application(Base):
    __tablename__ = "applications"
    __table_args__ = {"schema": "public"}

    job_seeker_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.users.user_id", ondelete="CASCADE"),
        primary_key=True
    )

    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("public.job.job_id", ondelete="CASCADE"),
        primary_key=True
    )

    applied_at = Column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    # Relationships
    job_seeker = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
