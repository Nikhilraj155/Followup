from datetime import datetime, timezone
from typing import Dict, Any
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.application import Application, ApplicationStatus
from app.models.followup import FollowUp, FollowUpStatus
from app.models.email_account import EmailAccount
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.services.reply_detector import ReplyDetectorService
from app.services.ai_service import AIService
from app.services.gmail_service import GmailService
from app.services.email_service import EmailDispatchService
from app.services.scheduler_service import SchedulerService
from app.core.logging import logger

@celery_app.task(name="app.workers.tasks.check_application_reply_task")
def check_application_reply_task(application_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            return {"status": "error", "message": "Application not found"}

        # Perform reply detection
        has_replied, reply_msg = ReplyDetectorService.check_for_hr_reply(db, application_id)
        if has_replied:
            return {
                "status": "stopped",
                "message": "HR replied. Follow-ups cancelled.",
                "application_id": application_id
            }

        # Find scheduled follow-up
        scheduled_fu = db.query(FollowUp).filter(
            FollowUp.application_id == application_id,
            FollowUp.status == FollowUpStatus.SCHEDULED.value
        ).order_by(FollowUp.follow_up_number.asc()).first()

        if scheduled_fu:
            # Generate AI draft if time has come
            now = datetime.now(timezone.utc)
            if scheduled_fu.scheduled_at <= now:
                generate_followup_task.delay(scheduled_fu.id)

        return {"status": "success", "hr_replied": False, "application_id": application_id}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.generate_followup_task")
def generate_followup_task(followup_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        fu = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
        if not fu or fu.status in [FollowUpStatus.SENT.value, FollowUpStatus.CANCELLED.value]:
            return {"status": "skipped", "reason": "Followup non-eligible"}

        app = fu.application
        if not app or app.status in [ApplicationStatus.REPLIED.value, ApplicationStatus.CLOSED.value, ApplicationStatus.CANCELLED.value]:
            fu.status = FollowUpStatus.CANCELLED.value
            db.commit()
            return {"status": "cancelled", "reason": "Application inactive or replied"}

        # Safety Check: Reply Detection immediately before generating
        has_replied, _ = ReplyDetectorService.check_for_hr_reply(db, app.id)
        if has_replied:
            return {"status": "cancelled", "reason": "HR has already replied"}

        fu.status = FollowUpStatus.GENERATING.value
        db.commit()

        # Build context
        thread = app.email_thread
        messages = thread.emails if thread else []
        thread_context = [
            {
                "sender": m.sender,
                "body": m.body,
                "is_reply": m.email_type == EmailType.REPLY.value,
                "sender_type": "user" if m.sender == app.user.email else "hr"
            }
            for m in messages
        ]

        prev_followups = [
            {"number": f.follow_up_number, "sent_at": f.sent_at}
            for f in app.follow_ups if f.sent_at
        ]

        original_email = messages[0].body if messages else f"Applying for {app.job_title} position at {app.company}."

        contact_name = app.contact.name if app.contact else "Hiring Manager"

        ai_res = AIService.generate_followup(
            company=app.company,
            job_title=app.job_title,
            hr_name=contact_name,
            user_name=app.user.name,
            original_email=original_email,
            email_thread=thread_context,
            previous_followups=prev_followups,
            followup_number=fu.follow_up_number
        )

        if not ai_res.get("should_follow_up"):
            fu.status = FollowUpStatus.SKIPPED.value
            db.commit()
            return {"status": "skipped", "reason": ai_res.get("reason")}

        fu.subject = ai_res.get("subject")
        fu.body = ai_res.get("body")
        fu.generated_at = datetime.now(timezone.utc)
        fu.status = FollowUpStatus.DRAFT.value
        db.commit()

        logger.log_event("followup_generated", {
            "followup_id": fu.id,
            "application_id": app.id,
            "follow_up_number": fu.follow_up_number
        })

        # Check user auto_send and require_approval settings
        user_settings = SchedulerService.get_or_create_user_settings(db, app.user_id)
        if user_settings.auto_send and not user_settings.require_approval:
            fu.approved_by_user = True
            fu.status = FollowUpStatus.APPROVED.value
            db.commit()
            send_followup_task.delay(fu.id)

        return {"status": "success", "followup_id": fu.id}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.send_followup_task")
def send_followup_task(followup_id: int) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        fu = db.query(FollowUp).filter(FollowUp.id == followup_id).first()
        if not fu:
            return {"status": "error", "message": "FollowUp record not found"}

        # IDEMPOTENCY CHECK: Never resend an already sent follow-up!
        if fu.status == FollowUpStatus.SENT.value:
            logger.log_event("duplicate_send_prevented", {"followup_id": fu.id})
            return {"status": "skipped", "message": "Followup already sent"}

        app = fu.application
        if not app:
            return {"status": "error", "message": "Application not found"}

        # CRITICAL SAFETY CHECK: Re-verify HR reply right before actual dispatch!
        has_replied, _ = ReplyDetectorService.check_for_hr_reply(db, app.id)
        if has_replied or app.status in [ApplicationStatus.REPLIED.value, ApplicationStatus.CLOSED.value, ApplicationStatus.CANCELLED.value]:
            fu.status = FollowUpStatus.CANCELLED.value
            db.commit()
            return {"status": "cancelled", "reason": "HR replied or application closed prior to sending"}

        # Retrieve user email account
        account = db.query(EmailAccount).filter(
            EmailAccount.user_id == app.user_id,
            EmailAccount.provider == "gmail"
        ).first()

        recipient_email = app.contact.email if app.contact else "recruiter@example.com"
        thread = app.email_thread
        provider_thread_id = thread.provider_thread_id if thread else None

        # Find last message ID in thread for In-Reply-To header
        last_msg = thread.emails[-1] if thread and thread.emails else None
        in_reply_to_id = last_msg.provider_message_id if last_msg else None

        # Send via EmailDispatchService (Brevo API / Gmail API)
        send_res = EmailDispatchService.send_email(
            account=account,
            sender_email=app.user.email,
            sender_name=app.user.name,
            to_email=recipient_email,
            subject=fu.subject or f"Follow-up: {app.job_title} Application - {app.company}",
            body=fu.body or "",
            thread_id=provider_thread_id,
            in_reply_to_msg_id=in_reply_to_id
        )

        now = datetime.now(timezone.utc)
        fu.status = FollowUpStatus.SENT.value
        fu.sent_at = now
        db.add(fu)

        # Store sent email message in thread
        if thread:
            sent_email = Email(
                thread_id=thread.id,
                provider_message_id=send_res.get("message_id"),
                sender=account.email_address if account else app.user.email,
                receiver=recipient_email,
                subject=fu.subject or f"Follow-up #{fu.follow_up_number}",
                body=fu.body or "",
                email_type=EmailType.FOLLOW_UP.value,
                sent_at=now
            )
            db.add(sent_email)

        app.status = ApplicationStatus.WAITING.value
        app.updated_at = now
        db.add(app)
        db.commit()

        logger.log_event("followup_sent", {
            "followup_id": fu.id,
            "application_id": app.id,
            "follow_up_number": fu.follow_up_number
        })

        # Schedule subsequent follow-up stage
        SchedulerService.schedule_next_followup(db, app.id, from_time=now)

        return {"status": "success", "message_id": send_res.get("message_id")}
    except Exception as e:
        logger.log_event("email_send_failed", {"followup_id": followup_id, "error": str(e)}, level="error")
        if fu:
            fu.status = FollowUpStatus.FAILED.value
            db.commit()
        return {"status": "failed", "error": str(e)}
    finally:
        db.close()

@celery_app.task(name="app.workers.tasks.check_all_active_applications_reply_task")
def check_all_active_applications_reply_task() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        active_apps = db.query(Application).filter(
            Application.status.in_([ApplicationStatus.WAITING.value, ApplicationStatus.FOLLOW_UP_SCHEDULED.value])
        ).all()

        checked = 0
        replied_count = 0
        for app in active_apps:
            has_replied, _ = ReplyDetectorService.check_for_hr_reply(db, app.id)
            checked += 1
            if has_replied:
                replied_count += 1
            else:
                # If no reply, check if any scheduled follow-up is due
                scheduled_fu = db.query(FollowUp).filter(
                    FollowUp.application_id == app.id,
                    FollowUp.status == FollowUpStatus.SCHEDULED.value
                ).first()
                if scheduled_fu and scheduled_fu.scheduled_at <= datetime.now(timezone.utc):
                    generate_followup_task.delay(scheduled_fu.id)

        return {"checked": checked, "replied_detected": replied_count}
    finally:
        db.close()
