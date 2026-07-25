from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.app.database import db
from backend.app.schemas.settings import UserSettingsUpdate, UserSettingsResponse
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1/settings", tags=["Settings"])

@router.get("", response_model=APIResponse[UserSettingsResponse])
async def get_user_settings(current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    doc = await db.db.settings.find_one({"user_id": user_id})
    now = datetime.now(timezone.utc).isoformat()
    
    if not doc:
        doc = {
            "user_id": user_id,
            "theme": "dark",
            "language": "en",
            "notifications": True,
            "updated_at": now
        }
        await db.db.settings.insert_one(doc)
        
    return APIResponse(
        success=True,
        message="Settings retrieved successfully",
        data=UserSettingsResponse(
            user_id=user_id,
            theme=doc.get("theme", "dark"),
            language=doc.get("language", "en"),
            notifications=doc.get("notifications", True),
            updated_at=str(doc.get("updated_at", now))
        )
    )

@router.put("", response_model=APIResponse[UserSettingsResponse])
async def update_user_settings(
    payload: UserSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    now = datetime.now(timezone.utc).isoformat()
    
    updates = {"updated_at": now}
    if payload.theme is not None:
        updates["theme"] = payload.theme
    if payload.language is not None:
        updates["language"] = payload.language
    if payload.notifications is not None:
        updates["notifications"] = payload.notifications
        
    await db.db.settings.update_one(
        {"user_id": user_id},
        {"$set": updates},
        upsert=True
    )
    
    updated = await db.db.settings.find_one({"user_id": user_id})
    
    return APIResponse(
        success=True,
        message="Settings updated successfully",
        data=UserSettingsResponse(
            user_id=user_id,
            theme=updated.get("theme", "dark"),
            language=updated.get("language", "en"),
            notifications=updated.get("notifications", True),
            updated_at=str(updated.get("updated_at", now))
        )
    )
