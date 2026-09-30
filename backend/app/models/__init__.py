from app.models.user import User
from app.models.email_account import EmailAccount
from app.models.contact import Contact
from app.models.application import Application, ApplicationStatus
from app.models.email_thread import EmailThread
from app.models.email import Email, EmailType
from app.models.followup import FollowUp, FollowUpStatus
from app.models.settings import AutomationSettings

__all__ = [
    "User",
    "EmailAccount",
    "Contact",
    "Application",
    "ApplicationStatus",
    "EmailThread",
    "Email",
    "EmailType",
    "FollowUp",
    "FollowUpStatus",
    "AutomationSettings",
]
