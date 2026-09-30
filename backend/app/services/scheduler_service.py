from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.models.application import Application, ApplicationStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.settings import AutomationSettings
from app.core.logging import logger

class SchedulerService:
    """
    Manages configurable follow-up rules, scheduling, and stage transitions.
    """

    @classmethod
    def get_or_create_user_settings(cls, db: Session, user_id: int) -> AutomationSettings:
        settings = db.query(AutomationSettings).filter(AutomationSettings.user_id == user_id).first()
        if not settings:
            settings = AutomationSettings(
                user_id=user_id,
                first_interval_hours=24,
                first_stage_followups=3,
                second_interval_days=5,
                maximum_followups=4,
                auto_send=False,
                require_approval=True,
                ai_enabled=True
            )
            db.add(settings)
            db.commit()
            db.refresh(settings)
        return settings

    @classmethod
    def schedule_next_followup(
        cls,
        db: Session,
        application_id: int,
        from_time: Optional[datetime] = None
    ) -> Optional[FollowUp]:
        """
        Schedules the next follow-up based on application status, current count, and user AutomationSettings.
        """
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return None

        # Do not schedule if application is in terminal or non-schedulable states
        if app.status in [ApplicationStatus.REPLIED.value, ApplicationStatus.CLOSED.value, ApplicationStatus.CANCELLED.value]:
            return None

        settings = cls.get_or_create_user_settings(db, app.user_id)

        # Count completed/sent/scheduled follow-ups
        existing_followups = db.query(FollowUp).filter(
            FollowUp.application_id == app.id
        ).order_by(FollowUp.follow_up_number.asc()).all()

        current_count = len([f for f in existing_followups if f.status in [FollowUpStatus.SENT.value, FollowUpStatus.APPROVED.value, FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value]])
        
        next_followup_number = current_count + 1

        # Check maximum follow-ups limit
        if next_followup_number > settings.maximum_followups:
            logger.log_event("max_followups_reached", {
                "application_id": app.id,
                "current_count": current_count,
                "max_limit": settings.maximum_followups
            })
            return None

        # Determine interval for next follow-up
        base_time = from_time or datetime.now(timezone.utc)
        
        if next_followup_number <= settings.first_stage_followups:
            delay = timedelta(hours=settings.first_interval_hours)
        else:
            delay = timedelta(days=settings.second_interval_days)

        scheduled_time = base_time + delay

        # Create scheduled follow-up
        followup = FollowUp(
            application_id=app.id,
            follow_up_number=next_followup_number,
            scheduled_at=scheduled_time,
            status=FollowUpStatus.SCHEDULED.value,
            ai_generated=settings.ai_enabled,
            approved_by_user=False
        )

        db.add(followup)

        # Update application status
        app.status = ApplicationStatus.FOLLOW_UP_SCHEDULED.value
        app.updated_at = datetime.now(timezone.utc)
        db.add(app)

        db.commit()
        db.refresh(followup)

        logger.log_event("followup_scheduled", {
            "application_id": app.id,
            "follow_up_number": next_followup_number,
            "scheduled_at": scheduled_time.isoformat()
        })

        return followup
