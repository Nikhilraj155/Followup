import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class ApplicationStatus(str, enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    WAITING = "waiting"
    REPLIED = "replied"
    FOLLOW_UP_SCHEDULED = "follow_up_scheduled"
    CLOSED = "closed"
    CANCELLED = "cancelled"

class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    contact_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True, index=True)
    company = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    status = Column(String(50), default=ApplicationStatus.WAITING.value, index=True, nullable=False)
    original_email_id = Column(Integer, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="applications")
    contact = relationship("Contact", back_populates="applications")
    email_thread = relationship("EmailThread", back_populates="application", uselist=False, cascade="all, delete-orphan")
    follow_ups = relationship("FollowUp", back_populates="application", cascade="all, delete-orphan")
