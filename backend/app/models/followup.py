import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class FollowUpStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    GENERATING = "generating"
    DRAFT = "draft"
    APPROVED = "approved"
    SENT = "sent"
    CANCELLED = "cancelled"
    FAILED = "failed"
    SKIPPED = "skipped"

class FollowUp(Base):
    __tablename__ = "follow_ups"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    follow_up_number = Column(Integer, nullable=False, default=1)
    scheduled_at = Column(DateTime(timezone=True), nullable=False, index=True)
    generated_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default=FollowUpStatus.SCHEDULED.value, index=True, nullable=False)
    ai_generated = Column(Boolean, default=True)
    approved_by_user = Column(Boolean, default=False)
    subject = Column(String(500), nullable=True)
    body = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    application = relationship("Application", back_populates="follow_ups")
