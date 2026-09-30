from typing import Tuple, Optional, List
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.models.application import Application, ApplicationStatus
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.models.followup import FollowUp, FollowUpStatus
from app.core.logging import logger

class ReplyDetectorService:
    """
    Service responsible for detecting recruiter replies in email threads and stopping automation when HR responds.
    """

    @classmethod
    def check_for_hr_reply(cls, db: Session, application_id: int) -> Tuple[bool, Optional[Email]]:
        """
        Inspects application's email thread messages to determine if HR / recruiter has replied.
        Returns (has_replied, reply_email_object).
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app or not app.email_thread:
            return False, None

        user_email = app.user.email.lower() if app.user and app.user.email else ""
        thread = app.email_thread

        # Retrieve all messages in thread sorted by date
        messages: List[Email] = db.query(Email).filter(
            Email.thread_id == thread.id
        ).order_by(Email.created_at.asc()).all()

        if not messages:
            return False, None

        # Determine reference sent time (initial email or app creation time)
        initial_time = app.sent_at or app.created_at

        # Check messages after initial application email
        for msg in messages:
            sender_addr = cls._extract_email_address(msg.sender)
            
            # If email is marked explicitly as reply, or sender is not user and not empty
            if msg.email_type == EmailType.REPLY.value:
                cls._handle_hr_reply_detected(db, app, msg)
                return True, msg

            if sender_addr and sender_addr != user_email and msg.email_type != EmailType.INITIAL.value:
                # Extra check: make sure message was received after application sent time or created after initial email
                msg_time = msg.sent_at or msg.received_at or msg.created_at
                if msg_time and msg_time >= initial_time:
                    # Update message type if needed
                    if msg.email_type != EmailType.REPLY.value:
                        msg.email_type = EmailType.REPLY.value
                        db.add(msg)
                    
                    cls._handle_hr_reply_detected(db, app, msg)
                    return True, msg

        return False, None

    @classmethod
    def _handle_hr_reply_detected(cls, db: Session, app: Application, reply_email: Email):
        """
        Performs atomic cancellation of all pending follow-ups and updates application status to REPLIED.
        """
        if app.status != ApplicationStatus.REPLIED.value:
            app.status = ApplicationStatus.REPLIED.value
            app.updated_at = datetime.now(timezone.utc)
            db.add(app)

        # Cancel all pending/scheduled/draft followups
        pending_followups = db.query(FollowUp).filter(
            FollowUp.application_id == app.id,
            FollowUp.status.in_([FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value, FollowUpStatus.GENERATING.value])
        ).all()

        for fu in pending_followups:
            fu.status = FollowUpStatus.CANCELLED.value
            fu.updated_at = datetime.now(timezone.utc)
            db.add(fu)

        db.commit()

        logger.log_event("hr_reply_detected", {
            "application_id": app.id,
            "company": app.company,
            "sender": reply_email.sender,
            "subject": reply_email.subject
        })

    @staticmethod
    def _extract_email_address(raw: str) -> str:
        if not raw:
            return ""
        if "<" in raw and ">" in raw:
            return raw.split("<")[1].split(">")[0].strip().lower()
        return raw.strip().lower()
