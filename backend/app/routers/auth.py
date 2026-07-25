from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.user import UserRegister, UserLogin, UserResponse, TokenResponse, UserProfileUpdate
from backend.app.schemas.common import APIResponse
from backend.app.utils.security import hash_password, verify_password, create_access_token
from backend.app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Authentication"])

def format_user_doc(user_doc: dict) -> UserResponse:
    return UserResponse(
        id=str(user_doc["_id"]),
        name=user_doc.get("name", ""),
        email=user_doc.get("email", ""),
        role=user_doc.get("role", "User"),
        profile_image=user_doc.get("profile_image", ""),
        created_at=str(user_doc.get("created_at", "")),
        updated_at=str(user_doc.get("updated_at", ""))
    )

@router.post("/register", response_model=APIResponse[TokenResponse])
async def register_user(payload: UserRegister):
    # Check if user already exists
    existing = await db.db.users.find_one({"email": payload.email.lower()})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    now = datetime.now(timezone.utc).isoformat()
    new_user = {
        "name": payload.name,
        "email": payload.email.lower(),
        "password": hash_password(payload.password),
        "role": payload.role if payload.role in ["User", "Admin"] else "User",
        "profile_image": "",
        "created_at": now,
        "updated_at": now
    }
    
    res = await db.db.users.insert_one(new_user)
    new_user["_id"] = res.inserted_id
    
    token = create_access_token({"sub": str(res.inserted_id), "email": new_user["email"], "role": new_user["role"]})
    user_resp = format_user_doc(new_user)
    
    return APIResponse(
        success=True,
        message="User registered successfully",
        data=TokenResponse(access_token=token, user=user_resp)
    )

@router.post("/login", response_model=APIResponse[TokenResponse])
async def login_user(payload: UserLogin):
    user = await db.db.users.find_one({"email": payload.email.lower()})
    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"], "role": user["role"]})
    user_resp = format_user_doc(user)
    
    return APIResponse(
        success=True,
        message="User logged in successfully",
        data=TokenResponse(access_token=token, user=user_resp)
    )

@router.post("/logout", response_model=APIResponse[dict])
async def logout_user(current_user: dict = Depends(get_current_user)):
    return APIResponse(
        success=True,
        message="User logged out successfully",
        data={"user_id": current_user["id"]}
    )

@router.get("/profile", response_model=APIResponse[UserResponse])
async def get_profile(current_user: dict = Depends(get_current_user)):
    return APIResponse(
        success=True,
        message="Profile retrieved successfully",
        data=format_user_doc(current_user)
    )

@router.put("/profile", response_model=APIResponse[UserResponse])
async def update_profile(payload: UserProfileUpdate, current_user: dict = Depends(get_current_user)):
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.name is not None:
        updates["name"] = payload.name
    if payload.profile_image is not None:
        updates["profile_image"] = payload.profile_image
    
    await db.db.users.update_one({"_id": ObjectId(current_user["id"])}, {"$set": updates})
    updated_user = await db.db.users.find_one({"_id": ObjectId(current_user["id"])})
    
    return APIResponse(
        success=True,
        message="Profile updated successfully",
        data=format_user_doc(updated_user)
    )
