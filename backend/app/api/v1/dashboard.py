from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.followup import FollowUp, FollowUpStatus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    total_apps = db.query(Application).filter(Application.user_id == current_user.id).count()
    waiting_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status.in_([ApplicationStatus.WAITING.value, ApplicationStatus.SENT.value])
    ).count()
    hr_replies = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status == ApplicationStatus.REPLIED.value
    ).count()
    scheduled_followups = db.query(FollowUp).join(Application).filter(
        Application.user_id == current_user.id,
        FollowUp.status.in_([FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value, FollowUpStatus.APPROVED.value])
    ).count()
    completed_apps = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.status.in_([ApplicationStatus.REPLIED.value, ApplicationStatus.CLOSED.value, ApplicationStatus.CANCELLED.value])
    ).count()

    return {
        "total_applications": total_apps,
        "waiting_for_response": waiting_apps,
        "hr_replies": hr_replies,
        "scheduled_followups": scheduled_followups,
        "completed_applications": completed_apps
    }
