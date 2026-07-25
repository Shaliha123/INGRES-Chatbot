from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.user import UserResponse, UserProfileUpdate
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import require_admin
from backend.app.routers.auth import format_user_doc

router = APIRouter(prefix="/api/v1/users", tags=["User Management"])

@router.get("", response_model=APIResponse[List[UserResponse]])
async def list_users(admin_user: dict = Depends(require_admin)):
    cursor = db.db.users.find()
    users_list = []
    async for doc in cursor:
        users_list.append(format_user_doc(doc))
    
    return APIResponse(
        success=True,
        message=f"Retrieved {len(users_list)} users",
        data=users_list
    )

@router.put("/{user_id}", response_model=APIResponse[UserResponse])
async def update_user(user_id: str, payload: UserProfileUpdate, admin_user: dict = Depends(require_admin)):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    existing = await db.db.users.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.role is not None:
        if payload.role not in ["User", "Admin"]:
            raise HTTPException(status_code=400, detail="Role must be 'User' or 'Admin'")
        updates["role"] = payload.role
    if payload.profile_image is not None:
        updates["profile_image"] = payload.profile_image
        
    await db.db.users.update_one({"_id": obj_id}, {"$set": updates})
    updated = await db.db.users.find_one({"_id": obj_id})
    
    return APIResponse(
        success=True,
        message="User updated successfully",
        data=format_user_doc(updated)
    )

@router.delete("/{user_id}", response_model=APIResponse[dict])
async def delete_user(user_id: str, admin_user: dict = Depends(require_admin)):
    try:
        obj_id = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    
    res = await db.db.users.delete_one({"_id": obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return APIResponse(
        success=True,
        message="User deleted successfully",
        data={"user_id": user_id}
    )
