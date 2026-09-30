import base64
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from app.core.config import settings
from app.models.email_account import EmailAccount
from app.services.gmail_service import GmailService
from app.services.brevo_service import BrevoEmailService
from app.core.logging import logger

class EmailDispatchService:
    """
    Unified Email Dispatch Service routing messages through Gmail App Password SMTP, Brevo API, Gmail OAuth, or fallback.
    """

    @classmethod
    def send_email(
        cls,
        account: Optional[EmailAccount],
        sender_email: str,
        sender_name: str,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to_msg_id: Optional[str] = None,
        attachment_path: Optional[str] = None
    ) -> Dict[str, str]:
        
        # Priority 1: Gmail App Password SMTP (Direct email from nikhilrajjatav@gmail.com)
        if settings.GMAIL_APP_PASSWORD:
            try:
                msg = MIMEMultipart()
                from_addr = settings.GMAIL_SENDER_EMAIL or sender_email
                msg['From'] = f"{sender_name} <{from_addr}>"
                msg['To'] = to_email
                msg['Subject'] = subject

                if in_reply_to_msg_id:
                    msg['In-Reply-To'] = in_reply_to_msg_id
                    msg['References'] = in_reply_to_msg_id

                msg.attach(MIMEText(body, 'plain'))

                if attachment_path and os.path.exists(attachment_path):
                    filename = os.path.basename(attachment_path)
                    with open(attachment_path, "rb") as f:
                        part = MIMEBase("application", "octet-stream")
                        part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                    msg.attach(part)

                with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as server:
                    server.starttls()
                    server.login(from_addr, settings.GMAIL_APP_PASSWORD)
                    server.send_message(msg)

                msg_id = f"gmail_smtp_{int(datetime.now(timezone.utc).timestamp())}"
                logger.log_event("email_sent", {"to": to_email, "subject": subject, "provider": "gmail_smtp"})
                return {
                    "message_id": msg_id,
                    "thread_id": thread_id or f"thread_{msg_id}"
                }
            except Exception as e:
                logger.log_event("gmail_smtp_error", {"error": str(e)}, level="warning")

        # Priority 2: Use Brevo API / SMTP
        if settings.BREVO_API_KEY:
            res = BrevoEmailService.send_email(
                to_email=to_email,
                subject=subject,
                body=body,
                sender_email=account.email_address if account and account.email_address else sender_email,
                sender_name=sender_name,
                in_reply_to_msg_id=in_reply_to_msg_id,
                attachment_path=attachment_path
            )
            return {
                "message_id": res.get("message_id"),
                "thread_id": thread_id or f"thread_{res.get('message_id')}"
            }

        # Priority 3: Use Gmail OAuth API
        return GmailService.send_email(
            account=account,
            to_email=to_email,
            subject=subject,
            body=body,
            thread_id=thread_id,
            in_reply_to_msg_id=in_reply_to_msg_id,
            attachment_path=attachment_path
        )
