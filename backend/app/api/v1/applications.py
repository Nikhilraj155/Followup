from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.contact import Contact
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.models.followup import FollowUp, FollowUpStatus
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationOut, ApplicationDetailOut
from app.services.scheduler_service import SchedulerService
from app.services.reply_detector import ReplyDetectorService

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("", response_model=ApplicationDetailOut, status_code=status.HTTP_201_CREATED)
def create_application(
    app_in: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Find or create contact
    contact = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.email == app_in.hr_email.lower()
    ).first()

    if not contact:
        contact = Contact(
            user_id=current_user.id,
            name=app_in.hr_name,
            email=app_in.hr_email.lower(),
            company=app_in.company
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # Create application
    now = datetime.now(timezone.utc)
    app = Application(
        user_id=current_user.id,
        contact_id=contact.id,
        company=app_in.company,
        job_title=app_in.job_title,
        status=ApplicationStatus.WAITING.value,
        sent_at=now
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    # Create initial email thread & message
    subject = app_in.subject or f"Application for {app_in.job_title} position"
    initial_body = app_in.initial_email_body or f"Dear {app_in.hr_name},\n\nI am applying for the {app_in.job_title} position at {app_in.company}."

    thread = EmailThread(
        application_id=app.id,
        provider_thread_id=f"thread_{app.id}_{int(now.timestamp())}",
        subject=subject
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    initial_email = Email(
        thread_id=thread.id,
        provider_message_id=f"msg_init_{app.id}_{int(now.timestamp())}",
        sender=current_user.email,
        receiver=app_in.hr_email,
        subject=subject,
        body=initial_body,
        email_type=EmailType.INITIAL.value,
        sent_at=now
    )
    db.add(initial_email)
    app.original_email_id = initial_email.id
    db.commit()

    # Automatically schedule initial follow-up based on user rules
    SchedulerService.schedule_next_followup(db, app.id, from_time=now)

    db.refresh(app)
    return app

@router.get("", response_model=List[ApplicationOut])
def list_applications(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Application).filter(Application.user_id == current_user.id)
    if status_filter:
        query = query.filter(Application.status == status_filter)
    
    apps = query.order_by(Application.updated_at.desc()).all()

    # Enrich with computed next follow-up and follow-up count
    result = []
    for app in apps:
        next_fu = db.query(FollowUp).filter(
            FollowUp.application_id == app.id,
            FollowUp.status.in_([FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value])
        ).order_by(FollowUp.scheduled_at.asc()).first()

        fu_count = db.query(FollowUp).filter(
            FollowUp.application_id == app.id,
            FollowUp.status == FollowUpStatus.SENT.value
        ).count()

        app_dict = ApplicationOut.model_validate(app)
        app_dict.next_followup_at = next_fu.scheduled_at if next_fu else None
        app_dict.followup_count = fu_count
        result.append(app_dict)

    return result

@router.get("/{app_id}", response_model=ApplicationDetailOut)
def get_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    # Sync/Check for HR reply on view
    ReplyDetectorService.check_for_hr_reply(db, app.id)

    db.refresh(app)
    return app

@router.put("/{app_id}", response_model=ApplicationOut)
def update_application(
    app_id: int,
    app_in: ApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    if app_in.company is not None:
        app.company = app_in.company
    if app_in.job_title is not None:
        app.job_title = app_in.job_title
    if app_in.status is not None:
        app.status = app_in.status
        # If set to closed, cancelled, or replied, cancel pending follow-ups
        if app.status in [ApplicationStatus.CLOSED.value, ApplicationStatus.CANCELLED.value, ApplicationStatus.REPLIED.value]:
            pending = db.query(FollowUp).filter(
                FollowUp.application_id == app.id,
                FollowUp.status.in_([FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value])
            ).all()
            for fu in pending:
                fu.status = FollowUpStatus.CANCELLED.value
                db.add(fu)

    app.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(app)

    next_fu = db.query(FollowUp).filter(
        FollowUp.application_id == app.id,
        FollowUp.status.in_([FollowUpStatus.SCHEDULED.value, FollowUpStatus.DRAFT.value])
    ).first()
    fu_count = db.query(FollowUp).filter(
        FollowUp.application_id == app.id,
        FollowUp.status == FollowUpStatus.SENT.value
    ).count()

    out = ApplicationOut.model_validate(app)
    out.next_followup_at = next_fu.scheduled_at if next_fu else None
    out.followup_count = fu_count
    return out

@router.delete("/{app_id}")
def delete_application(
    app_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    app = db.query(Application).filter(
        Application.id == app_id,
        Application.user_id == current_user.id
    ).first()

    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    db.delete(app)
    db.commit()
    return {"success": True, "message": "Application deleted successfully."}
