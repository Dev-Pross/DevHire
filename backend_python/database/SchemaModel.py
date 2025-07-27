from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, Table, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
import uuid
from database.db_engine import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_email", "email"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(Text, unique=True, nullable=False)
    full_name = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class UploadedResume(Base):
    __tablename__ = "uploaded_resume"
    __table_args__ = (
        Index("idx_uploaded_resume_users_id", "users_id"),
        Index("idx_uploaded_resume_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_url = Column(Text)
    experience = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    users_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))

class ParsedTitle(Base):
    __tablename__ = "parsed_title"
    __table_args__ = (
        Index("idx_parsed_title_resume_id", "resume_id"),
        Index("idx_parsed_title_titles", "titles"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titles = Column(ARRAY(Text))
    keywords = Column(ARRAY(Text))
    resume_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_resume.id", ondelete="CASCADE", onupdate="CASCADE"))

class ScrapedJob(Base):
    __tablename__ = "scraped_jobs"
    __table_args__ = (
        Index("idx_scraped_jobs_title_company", "title", "company"),
        Index("idx_scraped_jobs_created_at", "created_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text)
    company = Column(Text)
    location = Column(Text)
    platform = Column(Text)
    job_url = Column(Text)
    job_desc = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ParsedTitleHasScrapedJobs(Base):
    __tablename__ = "parsed_title_has_scraped_jobs"

    title_id = Column(UUID(as_uuid=True), ForeignKey("parsed_title.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    jobs_id = Column(UUID(as_uuid=True), ForeignKey("scraped_jobs.id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)

class TailoredResume(Base):
    __tablename__ = "tailored_resume"
    __table_args__ = (
        Index("idx_tailored_resume_jobs_id", "jobs_id"),
        Index("idx_tailored_resume_resume_id", "resume_id"),
        Index("idx_tailored_resume_generated_at", "generated_at")
    )

    tailored_resume_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    file_url = Column(Text)
    generated_at = Column(DateTime, default=datetime.utcnow)
    jobs_id = Column(UUID(as_uuid=True), ForeignKey("scraped_jobs.id", ondelete="CASCADE", onupdate="CASCADE"))
    resume_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_resume.id", ondelete="CASCADE", onupdate="CASCADE"))

class JobApplication(Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        Index("idx_job_applications_user_id", "users_id"),
        Index("idx_job_applications_status", "status"),
        Index("idx_job_applications_applied_at", "applied_at"),
        Index("idx_job_applications_resume_id", "uploaded_resume_id")
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(45))
    applied_at = Column(DateTime, default=datetime.utcnow)
    jobs_id = Column(UUID(as_uuid=True), ForeignKey("scraped_jobs.id", ondelete="CASCADE", onupdate="CASCADE"))
    tailored_resume_id = Column(UUID(as_uuid=True), ForeignKey("tailored_resume.tailored_resume_id", ondelete="CASCADE", onupdate="CASCADE"))
    users_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE", onupdate="CASCADE"))
    uploaded_resume_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_resume.id", ondelete="CASCADE", onupdate="CASCADE"))

class PipelineProgress(Base):
    __tablename__ = "pipeline_progress"
    __table_args__ = (
        Index("idx_pipeline_uploaded_resume_id", "uploaded_resume_id"),
        Index("idx_pipeline_current_stage", "current_stage"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    current_stage = Column(String(45))
    updated_at = Column(DateTime, default=datetime.utcnow)
    uploaded_resume_id = Column(UUID(as_uuid=True), ForeignKey("uploaded_resume.id", ondelete="CASCADE", onupdate="CASCADE"))
