from typing import Optional
from pydantic import BaseModel

class UserSettingsUpdate(BaseModel):
    theme: Optional[str] = "dark"
    language: Optional[str] = "en"
    notifications: Optional[bool] = True

class UserSettingsResponse(BaseModel):
    user_id: str
    theme: str
    language: str
    notifications: bool
    updated_at: str
