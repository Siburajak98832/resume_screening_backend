from pydantic import BaseModel,EmailStr
from typing import Optional
from datetime import datetime

# ------------------- ResumeLogCreate -------------------

class ResumeLogCreate(BaseModel):
    name: Optional[str]
    email: str
    role: Optional[str]
    level: Optional[str]
    final_score: Optional[float]
    status: Optional[str]

# ------------------- EmailRequest -------------------

class EmailRequest(BaseModel):
    email: str
    name: str
    status: str
    best_role: str
    score: float
    job_id :int
    sender_email: str
    sender_password: str
# ------------------- JobCreate -------------------

class JobCreate(BaseModel):
    title: str
    description: Optional[str]
    department: Optional[str]
    location: Optional[str]
    deadline: datetime
    required_skills: Optional[str]
    company_name: str
    created_by: str  # ✅ Admin UID or Email

class AdminConfigCreate(BaseModel):
    email: EmailStr
    smtp_host: str
    smtp_port: str
    smtp_username: str
    smtp_password: str

class AdminConfigOut(BaseModel):
    email: EmailStr
    smtp_host: str
    smtp_port: str
    smtp_username: str

    class Config:
        from_attributes = True

class JobOut(BaseModel):
    id: int
    title: str
    description: Optional[str]
    department: Optional[str]
    location: Optional[str]
    deadline: datetime
    required_skills: Optional[str]
    company_name: str
    created_by: str  # ✅ Returned to frontend

    class Config:
        from_attributes = True  # for ORM integration


