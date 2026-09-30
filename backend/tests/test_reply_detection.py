from datetime import datetime, timezone
from app.models.application import Application, ApplicationStatus
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.models.followup import FollowUp, FollowUpStatus
from app.services.reply_detector import ReplyDetectorService

def test_reply_detection_and_cancellation(db_session, test_user):
    # Setup application
    app = Application(
        user_id=test_user.id,
        company="TechCorp",
        job_title="Software Engineer",
        status=ApplicationStatus.WAITING.value
    )
    db_session.add(app)
    db_session.commit()

    thread = EmailThread(application_id=app.id, subject="Software Engineer Application")
    db_session.add(thread)
    db_session.commit()

    init_email = Email(
        thread_id=thread.id,
        sender=test_user.email,
        receiver="hr@techcorp.com",
        subject="Software Engineer Application",
        body="Applying for job",
        email_type=EmailType.INITIAL.value
    )
    db_session.add(init_email)

    fu = FollowUp(
        application_id=app.id,
        follow_up_number=1,
        scheduled_at=datetime.now(timezone.utc),
        status=FollowUpStatus.SCHEDULED.value
    )
    db_session.add(fu)
    db_session.commit()

    # Verify initial state: no reply
    has_replied, _ = ReplyDetectorService.check_for_hr_reply(db_session, app.id)
    assert has_replied is False
    assert app.status == ApplicationStatus.WAITING.value

    # Simulate HR reply
    reply_email = Email(
        thread_id=thread.id,
        sender="hr@techcorp.com",
        receiver=test_user.email,
        subject="Re: Software Engineer Application",
        body="Thanks for applying! We'd love to schedule an interview.",
        email_type=EmailType.REPLY.value,
        sent_at=datetime.now(timezone.utc)
    )
    db_session.add(reply_email)
    db_session.commit()

    # Test reply detection
    has_replied_now, msg = ReplyDetectorService.check_for_hr_reply(db_session, app.id)
    assert has_replied_now is True
    assert msg.sender == "hr@techcorp.com"

    # Verify application status and follow-up cancellation
    db_session.refresh(app)
    db_session.refresh(fu)
    assert app.status == ApplicationStatus.REPLIED.value
    assert fu.status == FollowUpStatus.CANCELLED.value
