from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.schemas.email import EmailThreadOut
from app.schemas.followup import FollowUpOut

class ContactBase(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None

class ContactOut(ContactBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ApplicationBase(BaseModel):
    company: str
    job_title: str

class ApplicationCreate(ApplicationBase):
    hr_name: str
    hr_email: EmailStr
    subject: Optional[str] = None
    initial_email_body: Optional[str] = None

class ApplicationUpdate(BaseModel):
    company: Optional[str] = None
    job_title: Optional[str] = None
    status: Optional[str] = None

class ApplicationOut(ApplicationBase):
    id: int
    user_id: int
    contact_id: Optional[int] = None
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    contact: Optional[ContactOut] = None
    next_followup_at: Optional[datetime] = None
    followup_count: int = 0

    class Config:
        from_attributes = True

class ApplicationDetailOut(ApplicationOut):
    email_thread: Optional[EmailThreadOut] = None
    follow_ups: List[FollowUpOut] = []
