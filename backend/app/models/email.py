import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class EmailType(str, enum.Enum):
    INITIAL = "initial"
    REPLY = "reply"
    FOLLOW_UP = "follow_up"
    DRAFT = "draft"

class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("email_threads.id", ondelete="CASCADE"), nullable=False, index=True)
    provider_message_id = Column(String(255), nullable=True, index=True)
    sender = Column(String(255), nullable=False)
    receiver = Column(String(255), nullable=False)
    subject = Column(String(500), nullable=False)
    body = Column(Text, nullable=False)
    email_type = Column(String(50), default=EmailType.INITIAL.value, nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    received_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    thread = relationship("EmailThread", back_populates="emails")
