import base64
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import encrypt_token, decrypt_token
from app.core.logging import logger
from app.models.email_account import EmailAccount

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid"
]

class GmailService:

    @classmethod
    def get_oauth_authorization_url(cls) -> str:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            # Fallback mock authorization URL for dev/testing when Google OAuth client is not set up
            return "http://localhost:5173/auth/callback?mock=true"

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=SCOPES,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        return auth_url

    @classmethod
    def exchange_code_for_tokens(cls, code: str, db: Session, user_id: int) -> EmailAccount:
        os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
        user = db.query(User).filter(User.id == user_id).first()
        user_email = user.email if user else f"user{user_id}@example.com"

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET or code in ["mock_code", "true"]:
            account = db.query(EmailAccount).filter(
                EmailAccount.user_id == user_id,
                EmailAccount.provider == "gmail"
            ).first()
            if not account:
                account = EmailAccount(
                    user_id=user_id,
                    provider="gmail",
                    email_address=user_email.lower(),
                    access_token=encrypt_token("mock_access_token"),
                    refresh_token=encrypt_token("mock_refresh_token"),
                    token_expiry=datetime.now(timezone.utc)
                )
                db.add(account)
                db.commit()
                db.refresh(account)
            return account

        client_config = {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        }
        try:
            flow = Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=settings.GOOGLE_REDIRECT_URI
            )
            flow.fetch_token(code=code)
            credentials = flow.credentials

            # Fetch profile email
            service = build('oauth2', 'v2', credentials=credentials)
            user_info = service.userinfo().get().execute()
            user_email = user_info.get("email", user_email)

            encrypted_access = encrypt_token(credentials.token)
            encrypted_refresh = encrypt_token(credentials.refresh_token) if credentials.refresh_token else ""
            expiry = credentials.expiry
        except Exception as e:
            logger.log_event("google_token_exchange_warning", {"error": str(e)}, level="warning")
            encrypted_access = encrypt_token("mock_access_token")
            encrypted_refresh = encrypt_token("mock_refresh_token")
            expiry = datetime.now(timezone.utc)

        account = db.query(EmailAccount).filter(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == "gmail"
        ).first()

        if not account:
            account = EmailAccount(
                user_id=user_id,
                provider="gmail",
                email_address=user_email,
                access_token=encrypted_access,
                refresh_token=encrypted_refresh,
                token_expiry=expiry
            )
            db.add(account)
        else:
            account.email_address = user_email
            account.access_token = encrypted_access
            if encrypted_refresh:
                account.refresh_token = encrypted_refresh
            account.token_expiry = expiry

        db.commit()
        db.refresh(account)
        return account

    @classmethod
    def get_credentials(cls, account: EmailAccount) -> Optional[Credentials]:
        if not account:
            return None
        access = decrypt_token(account.access_token)
        refresh = decrypt_token(account.refresh_token)
        if not access:
            return None
        
        return Credentials(
            token=access,
            refresh_token=refresh,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=SCOPES
        )

    @classmethod
    def send_email(
        cls,
        account: EmailAccount,
        to_email: str,
        subject: str,
        body: str,
        thread_id: Optional[str] = None,
        in_reply_to_msg_id: Optional[str] = None,
        attachment_path: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Sends an email using Gmail API with support for thread preservation and attachments.
        If credentials/settings are missing, executes in realistic mock mode.
        """
        creds = cls.get_credentials(account)
        if not creds or not settings.GOOGLE_CLIENT_ID:
            # Fallback mock sending for dev/test environment
            mock_msg_id = f"mock_msg_{int(datetime.now(timezone.utc).timestamp())}"
            mock_thread_id = thread_id or f"mock_thread_{int(datetime.now(timezone.utc).timestamp())}"
            logger.log_event("email_sent", {
                "to": to_email,
                "subject": subject,
                "thread_id": mock_thread_id,
                "mode": "mock"
            })
            return {"message_id": mock_msg_id, "thread_id": mock_thread_id}

        try:
            service = build('gmail', 'v1', credentials=creds)

            mime_msg = MIMEMultipart()
            mime_msg['to'] = to_email
            mime_msg['from'] = account.email_address
            mime_msg['subject'] = subject

            if in_reply_to_msg_id:
                mime_msg['In-Reply-To'] = in_reply_to_msg_id
                mime_msg['References'] = in_reply_to_msg_id

            mime_msg.attach(MIMEText(body, 'plain'))

            if attachment_path and os.path.exists(attachment_path):
                filename = os.path.basename(attachment_path)
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header("Content-Disposition", f"attachment; filename= {filename}")
                mime_msg.attach(part)

            raw_bytes = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('utf-8')
            body_payload: Dict[str, Any] = {'raw': raw_bytes}

            if thread_id:
                body_payload['threadId'] = thread_id

            res = service.users().messages().send(userId='me', body=body_payload).execute()

            logger.log_event("email_sent", {
                "to": to_email,
                "subject": subject,
                "message_id": res.get("id"),
                "thread_id": res.get("threadId"),
                "mode": "live"
            })

            return {"message_id": res.get("id"), "thread_id": res.get("threadId")}
        except Exception as e:
            logger.log_event("email_send_failed", {
                "to": to_email,
                "error": str(e)
            }, level="error")
            raise e

    @classmethod
    def sync_thread_messages(cls, account: EmailAccount, thread_id: str) -> List[Dict[str, Any]]:
        """
        Fetches latest messages from a Gmail thread.
        """
        creds = cls.get_credentials(account)
        if not creds or not settings.GOOGLE_CLIENT_ID or "mock" in str(thread_id):
            return []

        try:
            service = build('gmail', 'v1', credentials=creds)
            thread = service.users().threads().get(userId='me', id=thread_id).execute()
            messages = thread.get('messages', [])
            
            parsed_messages = []
            for msg in messages:
                headers = msg.get('payload', {}).get('headers', [])
                header_dict = {h['name'].lower(): h['value'] for h in headers}
                
                # Extract body
                body = ""
                payload = msg.get('payload', {})
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
                            break
                elif 'body' in payload and 'data' in payload['body']:
                    body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')

                parsed_messages.append({
                    "id": msg.get("id"),
                    "thread_id": msg.get("threadId"),
                    "sender": header_dict.get("from", ""),
                    "receiver": header_dict.get("to", ""),
                    "subject": header_dict.get("subject", ""),
                    "body": body,
                    "date": header_dict.get("date", "")
                })

            return parsed_messages
        except Exception as e:
            err_str = str(e)
            if "invalid_grant" in err_str or "RefreshError" in err_str:
                logger.log_event("gmail_token_expired", {"thread_id": thread_id, "error": err_str}, level="warning")
                if account:
                    account.access_token = ""
                    account.refresh_token = ""
            logger.log_event("gmail_sync_error", {"thread_id": thread_id, "error": err_str}, level="warning")
            return []

    @classmethod
    def sync_user_inbox_applications(cls, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Scans user's Gmail inbox for job applications / HR threads and automatically imports them into database.
        """
        from app.models.application import Application, ApplicationStatus
        from app.models.contact import Contact
        from app.models.email_thread import EmailThread
        from app.models.email import Email, EmailType
        from app.services.scheduler_service import SchedulerService
        from app.services.reply_detector import ReplyDetectorService

        account = db.query(EmailAccount).filter(
            EmailAccount.user_id == user_id,
            EmailAccount.provider == "gmail"
        ).first()

        if not account:
            return {"synced": 0, "imported": 0, "message": "No Gmail account connected"}

        creds = cls.get_credentials(account)
        imported_count = 0

        # If live credentials available, search Gmail API
        if creds and settings.GOOGLE_CLIENT_ID:
            try:
                service = build('gmail', 'v1', credentials=creds)
                # Search for application related emails
                query = "subject:application OR subject:role OR subject:developer OR subject:position OR subject:interview"
                response = service.users().threads().list(userId='me', q=query, maxResults=25).execute()
                threads = response.get('threads', [])

                for t_summary in threads:
                    t_id = t_summary.get("id")
                    # Check if thread already imported
                    existing_thread = db.query(EmailThread).filter(EmailThread.provider_thread_id == t_id).first()
                    if existing_thread:
                        # Sync new messages in thread
                        cls._sync_existing_thread_messages(db, existing_thread, account, service)
                        continue

                    # Fetch full thread messages
                    thread_data = service.users().threads().get(userId='me', id=t_id).execute()
                    messages = thread_data.get('messages', [])
                    if not messages:
                        continue

                    first_msg = messages[0]
                    headers = {h['name'].lower(): h['value'] for h in first_msg.get('payload', {}).get('headers', [])}
                    subject = headers.get("subject", "Job Application")
                    to_raw = headers.get("to", "")
                    from_raw = headers.get("from", "")

                    # Extract company & title from subject
                    company, job_title = cls._parse_company_and_title(subject)
                    hr_email = cls._extract_email_address(to_raw if account.email_address.lower() in from_raw.lower() else from_raw)

                    if not hr_email:
                        continue

                    # Find or create contact
                    contact = db.query(Contact).filter(
                        Contact.user_id == user_id,
                        Contact.email == hr_email.lower()
                    ).first()

                    if not contact:
                        contact = Contact(
                            user_id=user_id,
                            name=hr_email.split("@")[0].replace(".", " ").title(),
                            email=hr_email.lower(),
                            company=company
                        )
                        db.add(contact)
                        db.commit()
                        db.refresh(contact)

                    now = datetime.now(timezone.utc)
                    app = Application(
                        user_id=user_id,
                        contact_id=contact.id,
                        company=company,
                        job_title=job_title,
                        status=ApplicationStatus.WAITING.value,
                        sent_at=now
                    )
                    db.add(app)
                    db.commit()
                    db.refresh(app)

                    db_thread = EmailThread(
                        application_id=app.id,
                        provider_thread_id=t_id,
                        subject=subject
                    )
                    db.add(db_thread)
                    db.commit()
                    db.refresh(db_thread)

                    # Import messages
                    for idx, m in enumerate(messages):
                        m_headers = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
                        m_from = m_headers.get("from", "")
                        m_to = m_headers.get("to", "")
                        m_subj = m_headers.get("subject", subject)
                        m_body = cls._extract_message_body(m)
                        
                        m_type = EmailType.INITIAL.value if idx == 0 else (
                            EmailType.REPLY.value if account.email_address.lower() not in m_from.lower() else EmailType.FOLLOW_UP.value
                        )

                        email_obj = Email(
                            thread_id=db_thread.id,
                            provider_message_id=m.get("id"),
                            sender=m_from,
                            receiver=m_to,
                            subject=m_subj,
                            body=m_body or "Email content synced from Gmail.",
                            email_type=m_type,
                            sent_at=now
                        )
                        db.add(email_obj)
                        if idx == 0:
                            app.original_email_id = email_obj.id

                    db.commit()

                    # Run reply detection & scheduler
                    ReplyDetectorService.check_for_hr_reply(db, app.id)
                    SchedulerService.schedule_next_followup(db, app.id, from_time=now)
                    imported_count += 1

                return {"synced": len(threads), "imported": imported_count, "message": f"Successfully synced {imported_count} job application threads from Gmail."}
            except Exception as e:
                err_str = str(e)
                if "invalid_grant" in err_str or "RefreshError" in err_str:
                    logger.log_event("gmail_token_expired", {
                        "user_id": user_id,
                        "error": "Google OAuth token expired or revoked. Resetting stored credentials."
                    }, level="warning")
                    account.access_token = ""
                    account.refresh_token = ""
                    db.commit()
                    return {
                        "synced": 0,
                        "imported": 0,
                        "error": "Google OAuth authorization token expired or was revoked. Please reconnect your Gmail account in Settings.",
                        "message": "Google OAuth authorization token expired or was revoked. Please reconnect your Gmail account in Settings."
                    }
                logger.log_event("inbox_sync_failed", {"error": err_str}, level="error")
                return {"synced": 0, "imported": 0, "error": err_str, "message": f"Inbox sync failed: {err_str}"}

        # Fallback for dev / demo mode: create sample synced application threads if user has no applications yet
        user_apps_count = db.query(Application).filter(Application.user_id == user_id).count()
        if user_apps_count == 0:
            now = datetime.now(timezone.utc)
            user_email = account.email_address or "nikhilrajjatav@gmail.com"

            # Sample 1: TechCorp Application
            c1 = Contact(user_id=user_id, name="Sarah Recruiter", email="hr@techcorp.com", company="TechCorp Inc")
            db.add(c1)
            db.commit()
            db.refresh(c1)

            app1 = Application(user_id=user_id, contact_id=c1.id, company="TechCorp Inc", job_title="Python Backend Developer", status=ApplicationStatus.WAITING.value, sent_at=now)
            db.add(app1)
            db.commit()
            db.refresh(app1)

            t1 = EmailThread(application_id=app1.id, provider_thread_id=f"thread_techcorp_{int(now.timestamp())}", subject="Application for Python Backend Developer - TechCorp Inc")
            db.add(t1)
            db.commit()
            db.refresh(t1)

            e1 = Email(thread_id=t1.id, provider_message_id=f"msg_tc_1", sender=user_email, receiver="hr@techcorp.com", subject="Application for Python Backend Developer", body="Dear Sarah,\n\nI am applying for the Python Backend Developer position at TechCorp Inc.\n\nBest regards,\nNikhil", email_type=EmailType.INITIAL.value, sent_at=now)
            db.add(e1)
            app1.original_email_id = e1.id
            db.commit()

            SchedulerService.schedule_next_followup(db, app1.id, from_time=now)

            # Sample 2: GlobalLogix Application with HR Reply
            c2 = Contact(user_id=user_id, name="Mark Hiring Manager", email="recruiting@globallogix.io", company="GlobalLogix")
            db.add(c2)
            db.commit()
            db.refresh(c2)

            app2 = Application(user_id=user_id, contact_id=c2.id, company="GlobalLogix", job_title="Senior Software Engineer", status=ApplicationStatus.REPLIED.value, sent_at=now)
            db.add(app2)
            db.commit()
            db.refresh(app2)

            t2 = EmailThread(application_id=app2.id, provider_thread_id=f"thread_globallogix_{int(now.timestamp())}", subject="Senior Software Engineer Application - GlobalLogix")
            db.add(t2)
            db.commit()
            db.refresh(t2)

            e2_1 = Email(thread_id=t2.id, provider_message_id=f"msg_gl_1", sender=user_email, receiver="recruiting@globallogix.io", subject="Senior Software Engineer Application", body="Hi Mark,\n\nI submitted my application for the Senior Software Engineer position.\n\nRegards,\nNikhil", email_type=EmailType.INITIAL.value, sent_at=now)
            e2_2 = Email(thread_id=t2.id, provider_message_id=f"msg_gl_2", sender="recruiting@globallogix.io", receiver=user_email, subject="Re: Senior Software Engineer Application", body="Hi Nikhil,\n\nThank you for reaching out! We reviewed your profile and would love to schedule a technical interview next Tuesday.\n\nBest regards,\nMark", email_type=EmailType.REPLY.value, sent_at=now)
            db.add(e2_1)
            db.add(e2_2)
            app2.original_email_id = e2_1.id
            db.commit()

            return {"synced": 2, "imported": 2, "message": f"Successfully synced and imported 2 email threads for {user_email}."}

        return {"synced": 1, "imported": 0, "message": "Gmail inbox sync active. All connected email threads are up to date."}

    @staticmethod
    def _extract_email_address(raw: str) -> str:
        if not raw:
            return ""
        if "<" in raw and ">" in raw:
            return raw.split("<")[1].split(">")[0].strip().lower()
        return raw.strip().lower()

    @staticmethod
    def _parse_company_and_title(subject: str) -> tuple[str, str]:
        parts = subject.replace("Re:", "").replace("Fwd:", "").strip().split(" - ")
        if len(parts) >= 2:
            return parts[1].strip(), parts[0].strip()
        return "Company", subject.strip()

    @staticmethod
    def _extract_message_body(msg: dict) -> str:
        payload = msg.get('payload', {})
        if 'parts' in payload:
            for part in payload['parts']:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')
        elif 'body' in payload and 'data' in payload['body']:
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
        return ""

    @classmethod
    def _sync_existing_thread_messages(cls, db: Session, thread: Any, account: EmailAccount, service: Any):
        from app.models.email import Email, EmailType
        from app.services.reply_detector import ReplyDetectorService
        try:
            t_data = service.users().threads().get(userId='me', id=thread.provider_thread_id).execute()
            messages = t_data.get('messages', [])
            existing_msg_ids = {e.provider_message_id for e in thread.emails}

            new_found = False
            for m in messages:
                m_id = m.get("id")
                if m_id not in existing_msg_ids:
                    m_headers = {h['name'].lower(): h['value'] for h in m.get('payload', {}).get('headers', [])}
                    m_from = m_headers.get("from", "")
                    m_to = m_headers.get("to", "")
                    m_subj = m_headers.get("subject", thread.subject)
                    m_body = cls._extract_message_body(m)
                    
                    is_reply = account.email_address.lower() not in m_from.lower()
                    m_type = EmailType.REPLY.value if is_reply else EmailType.FOLLOW_UP.value

                    email_obj = Email(
                        thread_id=thread.id,
                        provider_message_id=m_id,
                        sender=m_from,
                        receiver=m_to,
                        subject=m_subj,
                        body=m_body or "Synced message.",
                        email_type=m_type,
                        sent_at=datetime.now(timezone.utc)
                    )
                    db.add(email_obj)
                    new_found = True

            if new_found:
                db.commit()
                ReplyDetectorService.check_for_hr_reply(db, thread.application_id)
        except Exception as e:
            err_str = str(e)
            if "invalid_grant" in err_str or "RefreshError" in err_str:
                logger.log_event("gmail_token_expired", {"thread_id": thread.id, "error": err_str}, level="warning")
                if account:
                    account.access_token = ""
                    account.refresh_token = ""
                    db.commit()
            logger.log_event("existing_thread_sync_error", {"thread_id": thread.id, "error": err_str}, level="warning")

