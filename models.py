from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

# ==================== ResumeLog Model ====================

class ResumeLog(Base):
    __tablename__ = "resume_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, index=True)
    role = Column(String, nullable=True)
    experience_level = Column(String, nullable=True)    
    final_score = Column(Float, nullable=True)
    status = Column(String, nullable=True)
    
    job_id = Column(Integer, ForeignKey("jobs.id"))
    job = relationship("Job", backref="resumes")

# ==================== Job Model ====================

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String)
    department = Column(String)
    location = Column(String)
    deadline = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    required_skills = Column(String)
    company_name = Column(String, nullable=False, default="Not mentioned")
    
    # ✅ NEW FIELD TO ENABLE MULTI-ADMIN SUPPORT
    created_by = Column(String, nullable=False)  # Admin UID


from sqlalchemy import Column, String
from database import Base

class AdminConfig(Base):
    __tablename__ = "admin_config"

    email = Column(String, primary_key=True, index=True)
    smtp_host = Column(String, nullable=False)
    smtp_port = Column(String, nullable=False)
    smtp_username = Column(String, nullable=False)
    smtp_password = Column(String, nullable=False)  # You may encrypt this later
