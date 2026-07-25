from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from backend.app.database import db
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Operations"])

@router.get("/logs", response_model=APIResponse[List[dict]])
async def get_system_logs(
    limit: int = Query(50, ge=1, le=500),
    admin_user: dict = Depends(require_admin)
):
    cursor = db.db.logs.find().sort("timestamp", -1).limit(limit)
    logs = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        del doc["_id"]
        logs.append(doc)
        
    return APIResponse(
        success=True,
        message=f"Retrieved {len(logs)} audit log records",
        data=logs
    )
