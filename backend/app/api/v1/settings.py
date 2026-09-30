from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.settings import AutomationSettingsOut, AutomationSettingsUpdate
from app.services.scheduler_service import SchedulerService

router = APIRouter(prefix="/settings", tags=["Settings"])

@router.get("", response_model=AutomationSettingsOut)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = SchedulerService.get_or_create_user_settings(db, current_user.id)
    return settings

@router.put("", response_model=AutomationSettingsOut)
def update_user_settings(
    settings_in: AutomationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = SchedulerService.get_or_create_user_settings(db, current_user.id)
    
    settings.first_interval_hours = settings_in.first_interval_hours
    settings.first_stage_followups = settings_in.first_stage_followups
    settings.second_interval_days = settings_in.second_interval_days
    settings.maximum_followups = settings_in.maximum_followups
    settings.auto_send = settings_in.auto_send
    settings.require_approval = settings_in.require_approval
    settings.ai_enabled = settings_in.ai_enabled
    settings.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(settings)
    return settings
