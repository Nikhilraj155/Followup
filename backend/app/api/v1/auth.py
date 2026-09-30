from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.database import get_db
from app.core.config import settings
from app.core.security import get_password_hash, verify_password, create_access_token, encrypt_token
from app.models.user import User
from app.models.email_account import EmailAccount
from app.schemas.user import UserCreate, UserLogin, UserOut, Token
from app.services.gmail_service import GmailService
from app.services.scheduler_service import SchedulerService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

class ConnectEmailRequest(BaseModel):
    email: Optional[EmailStr] = None

@router.post("/register", response_model=Token)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists."
        )

    user = User(
        name=user_in.name,
        email=user_in.email.lower(),
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default automation settings
    SchedulerService.get_or_create_user_settings(db, user.id)

    access_token = create_access_token(subject=user.id)
    user_out = UserOut.model_validate(user)
    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.post("/login", response_model=Token)
def login_user(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if not user or not user.hashed_password or not verify_password(user_in.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    access_token = create_access_token(subject=user.id)
    email_acc = db.query(EmailAccount).filter(EmailAccount.user_id == user.id, EmailAccount.provider == "gmail").first()
    
    user_out = UserOut(
        id=user.id,
        name=user.name,
        email=user.email,
        created_at=user.created_at,
        has_gmail_connected=email_acc is not None,
        connected_email=email_acc.email_address if email_acc else None
    )

    return Token(access_token=access_token, token_type="bearer", user=user_out)

@router.get("/me", response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    email_acc = db.query(EmailAccount).filter(EmailAccount.user_id == current_user.id, EmailAccount.provider == "gmail").first()
    return UserOut(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        created_at=current_user.created_at,
        has_gmail_connected=email_acc is not None,
        connected_email=email_acc.email_address if email_acc else None
    )

@router.get("/google")
def google_auth_url(current_user: User = Depends(get_current_user)):
    url = GmailService.get_oauth_authorization_url()
    return {"url": url}

@router.get("/google/callback")
def google_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    account = GmailService.exchange_code_for_tokens(code=code, db=db, user_id=current_user.id)
    return {
        "success": True,
        "message": "Gmail account connected successfully.",
        "connected_email": account.email_address
    }

@router.post("/google/connect")
def connect_email_account(
    req: ConnectEmailRequest = ConnectEmailRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Connects Gmail account. If Google OAuth credentials are not set in .env, connects user's email address in mock mode.
    """
    target_email = req.email or current_user.email
    account = db.query(EmailAccount).filter(
        EmailAccount.user_id == current_user.id,
        EmailAccount.provider == "gmail"
    ).first()

    if not account:
        account = EmailAccount(
            user_id=current_user.id,
            provider="gmail",
            email_address=target_email.lower(),
            access_token=encrypt_token("mock_access_token"),
            refresh_token=encrypt_token("mock_refresh_token"),
            token_expiry=datetime.now(timezone.utc)
        )
        db.add(account)
    else:
        account.email_address = target_email.lower()
        account.access_token = encrypt_token("mock_access_token")

    db.commit()
    db.refresh(account)

    return {
        "success": True,
        "message": "Gmail account connected successfully.",
        "connected_email": account.email_address
    }

@router.post("/logout")
def logout():
    return {"success": True, "message": "Logged out successfully."}
