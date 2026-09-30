from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr
from app.models.email import EmailType

class EmailBase(BaseModel):
    sender: str
    receiver: str
    subject: str
    body: str
    email_type: str = EmailType.INITIAL.value

class EmailCreate(EmailBase):
    pass

class EmailOut(EmailBase):
    id: int
    thread_id: int
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EmailThreadOut(BaseModel):
    id: int
    application_id: int
    provider_thread_id: Optional[str] = None
    subject: str
    created_at: datetime
    updated_at: datetime
    emails: List[EmailOut] = []

    class Config:
        from_attributes = True

class SendEmailRequest(BaseModel):
    company: str
    job_title: str
    hr_name: str
    hr_email: EmailStr
    subject: str
    body: str
