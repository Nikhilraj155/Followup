from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.followup import FollowUpStatus

class FollowUpOut(BaseModel):
    id: int
    application_id: int
    follow_up_number: int
    scheduled_at: datetime
    generated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    status: str
    ai_generated: bool
    approved_by_user: bool
    subject: Optional[str] = None
    body: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FollowUpGenerateResponse(BaseModel):
    should_follow_up: bool
    reason: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None

class FollowUpUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body: Optional[str] = None
