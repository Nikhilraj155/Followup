from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.schemas.followup import FollowUpOut, FollowUpGenerateResponse, FollowUpUpdateRequest
from app.workers.tasks import generate_followup_task, send_followup_task
from app.services.reply_detector import ReplyDetectorService
from app.services.ai_service import AIService

router = APIRouter(prefix="/followups", tags=["Follow-ups"])

@router.get("", response_model=List[FollowUpOut])
def list_followups(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(FollowUp).join(Application).filter(Application.user_id == current_user.id)
    if status_filter:
        query = query.filter(FollowUp.status == status_filter)
    
    return query.order_by(FollowUp.scheduled_at.desc()).all()

@router.get("/{fu_id}", response_model=FollowUpOut)
def get_followup(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")
    return fu

@router.post("/{fu_id}/generate", response_model=FollowUpOut)
def generate_followup_draft(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    app = fu.application
    has_replied, _ = ReplyDetectorService.check_for_hr_reply(db, app.id)
    if has_replied:
        fu.status = FollowUpStatus.CANCELLED.value
        db.commit()
        raise HTTPException(status_code=400, detail="Cannot generate follow-up: Recruiter has already responded.")

    # Call AI Service synchronously for instant preview in UI
    thread = app.email_thread
    messages = thread.emails if thread else []
    thread_context = [
        {
            "sender": m.sender,
            "body": m.body,
            "is_reply": False,
            "sender_type": "user" if m.sender == current_user.email else "hr"
        }
        for m in messages
    ]
    prev_followups = [{"number": f.follow_up_number, "sent_at": f.sent_at} for f in app.follow_ups if f.sent_at]
    original_email = messages[0].body if messages else ""
    contact_name = app.contact.name if app.contact else "Hiring Manager"

    ai_res = AIService.generate_followup(
        company=app.company,
        job_title=app.job_title,
        hr_name=contact_name,
        user_name=current_user.name,
        original_email=original_email,
        email_thread=thread_context,
        previous_followups=prev_followups,
        followup_number=fu.follow_up_number
    )

    if not ai_res.get("should_follow_up"):
        fu.status = FollowUpStatus.SKIPPED.value
        db.commit()
        raise HTTPException(status_code=400, detail=ai_res.get("reason", "Follow-up not required"))

    fu.subject = ai_res.get("subject")
    fu.body = ai_res.get("body")
    fu.generated_at = datetime.now(timezone.utc)
    fu.status = FollowUpStatus.DRAFT.value
    db.commit()
    db.refresh(fu)

    return fu

@router.put("/{fu_id}", response_model=FollowUpOut)
def update_followup_content(
    fu_id: int,
    fu_in: FollowUpUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    if fu_in.subject is not None:
        fu.subject = fu_in.subject
    if fu_in.body is not None:
        fu.body = fu_in.body

    fu.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(fu)
    return fu

@router.post("/{fu_id}/approve", response_model=FollowUpOut)
def approve_followup(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    fu.approved_by_user = True
    fu.status = FollowUpStatus.APPROVED.value
    fu.updated_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger sending task
    send_followup_task.delay(fu.id)

    db.refresh(fu)
    return fu

@router.post("/{fu_id}/send", response_model=FollowUpOut)
def send_followup_now(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    # Synchronously send for immediate UI feedback
    res = send_followup_task(fu.id)
    if res.get("status") == "failed":
        raise HTTPException(status_code=500, detail=res.get("error", "Email send failed"))

    db.refresh(fu)
    return fu

@router.post("/{fu_id}/cancel", response_model=FollowUpOut)
def cancel_followup(
    fu_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    fu = db.query(FollowUp).join(Application).filter(
        FollowUp.id == fu_id,
        Application.user_id == current_user.id
    ).first()
    if not fu:
        raise HTTPException(status_code=404, detail="Follow-up not found")

    fu.status = FollowUpStatus.CANCELLED.value
    fu.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(fu)
    return fu
