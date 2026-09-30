import pytest
from unittest.mock import patch, MagicMock
from app.services.gmail_service import GmailService
from app.models.email_account import EmailAccount
from app.core.security import encrypt_token

def test_sync_user_inbox_invalid_grant_handling(db_session, test_user):
    # Create an email account with mock tokens
    account = EmailAccount(
        user_id=test_user.id,
        provider="gmail",
        email_address=test_user.email,
        access_token=encrypt_token("expired_access_token"),
        refresh_token=encrypt_token("invalid_refresh_token")
    )
    db_session.add(account)
    db_session.commit()

    # Mock build() to simulate Google API throwing invalid_grant RefreshError
    with patch("app.services.gmail_service.build") as mock_build, \
         patch("app.core.config.settings.GOOGLE_CLIENT_ID", "mock_client_id"):
        
        mock_service = MagicMock()
        mock_service.users().threads().list().execute.side_effect = Exception(
            "('invalid_grant: Bad Request', {'error': 'invalid_grant', 'error_description': 'Bad Request'})"
        )
        mock_build.return_value = mock_service

        result = GmailService.sync_user_inbox_applications(db_session, test_user.id)

        assert result["synced"] == 0
        assert "expired" in result["error"].lower() or "reconnect" in result["error"].lower()
        
        # Verify stored tokens were cleared from DB
        db_session.refresh(account)
        assert account.access_token == ""
        assert account.refresh_token == ""
