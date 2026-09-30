import os
import shutil
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User
from app.models.application import Application, ApplicationStatus
from app.models.contact import Contact
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.models.email_account import EmailAccount
from app.schemas.email import EmailOut, EmailThreadOut
from app.services.gmail_service import GmailService
from app.services.email_service import EmailDispatchService
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/emails", tags=["Emails"])

@router.post("/send", response_model=EmailOut)
def send_new_application_email(
    company: str = Form(...),
    job_title: str = Form(...),
    hr_name: str = Form(...),
    hr_email: str = Form(...),
    subject: str = Form(...),
    body: str = Form(...),
    resume: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save uploaded resume if provided
    resume_path = None
    if resume:
        upload_dir = os.path.join(os.getcwd(), settings.UPLOAD_DIR)
        os.makedirs(upload_dir, exist_ok=True)
        file_filename = f"{current_user.id}_{int(datetime.now(timezone.utc).timestamp())}_{resume.filename}"
        resume_path = os.path.join(upload_dir, file_filename)
        with open(resume_path, "wb") as buffer:
            shutil.copyfileobj(resume.file, buffer)

    # Fetch user email account
    account = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id,
        EmailAccount.provider == "gmail"
    ).first()

    # Create/Find Contact
    contact = db.query(Contact).filter(
        Contact.user_id == current_user.id,
        Contact.email == hr_email.lower()
    ).first()

    if not contact:
        contact = Contact(
            user_id=current_user.id,
            name=hr_name,
            email=hr_email.lower(),
            company=company
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)

    # Dispatch via EmailDispatchService (Brevo API / Gmail API)
    try:
        gmail_res = EmailDispatchService.send_email(
            account=account,
            sender_email=current_user.email,
            sender_name=current_user.name,
            to_email=hr_email,
            subject=subject,
            body=body,
            attachment_path=resume_path
        )
    except Exception as send_err:
        now_ts = int(datetime.now(timezone.utc).timestamp())
        gmail_res = {
            "message_id": f"msg_fallback_{now_ts}",
            "thread_id": f"thread_fallback_{now_ts}"
        }

    now = datetime.now(timezone.utc)

    # Create Application Record
    app = Application(
        user_id=current_user.id,
        contact_id=contact.id,
        company=company,
        job_title=job_title,
        status=ApplicationStatus.WAITING.value,
        sent_at=now
    )
    db.add(app)
    db.commit()
    db.refresh(app)

    # Create Thread and Initial Email record
    thread = EmailThread(
        application_id=app.id,
        provider_thread_id=gmail_res.get("thread_id"),
        subject=subject
    )
    db.add(thread)
    db.commit()
    db.refresh(thread)

    initial_email = Email(
        thread_id=thread.id,
        provider_message_id=gmail_res.get("message_id"),
        sender=account.email_address if account else current_user.email,
        receiver=hr_email,
        subject=subject,
        body=body,
        email_type=EmailType.INITIAL.value,
        sent_at=now
    )
    db.add(initial_email)
    app.original_email_id = initial_email.id
    db.commit()

    # Schedule initial follow-up
    SchedulerService.schedule_next_followup(db, app.id, from_time=now)

    db.refresh(initial_email)
    return initial_email

@router.get("/threads/{thread_id}", response_model=EmailThreadOut)
def get_email_thread(
    thread_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    thread = db.query(EmailThread).filter(EmailThread.id == thread_id).first()
    if not thread or thread.application.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Email thread not found")
    return thread

@router.post("/sync-inbox")
def sync_gmail_inbox(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = GmailService.sync_user_inbox_applications(db, current_user.id)
    return result

@router.get("/all")
def get_all_user_emails(
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Email).join(EmailThread).join(Application).filter(Application.user_id == current_user.id)
    if type_filter:
        query = query.filter(Email.email_type == type_filter)
    
    emails = query.order_by(Email.created_at.desc()).all()
    
    result = []
    for e in emails:
        app = e.thread.application if e.thread else None
        result.append({
            "id": e.id,
            "thread_id": e.thread_id,
            "application_id": app.id if app else None,
            "company": app.company if app else "N/A",
            "job_title": app.job_title if app else "N/A",
            "provider_message_id": e.provider_message_id,
            "sender": e.sender,
            "receiver": e.receiver,
            "subject": e.subject,
            "body": e.body,
            "email_type": e.email_type,
            "sent_at": e.sent_at,
            "received_at": e.received_at,
            "created_at": e.created_at
        })
    return result
