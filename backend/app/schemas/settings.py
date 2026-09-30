from datetime import datetime
from pydantic import BaseModel

class AutomationSettingsBase(BaseModel):
    first_interval_hours: int = 24
    first_stage_followups: int = 3
    second_interval_days: int = 5
    maximum_followups: int = 4
    auto_send: bool = False
    require_approval: bool = True
    ai_enabled: bool = True

class AutomationSettingsUpdate(BaseModel):
    first_interval_hours: int
    first_stage_followups: int
    second_interval_days: int
    maximum_followups: int
    auto_send: bool
    require_approval: bool
    ai_enabled: bool

class AutomationSettingsOut(AutomationSettingsBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
