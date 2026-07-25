from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from backend.app.database import db
from backend.app.schemas.analytics import DashboardStats, AnalyticsDetail
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user

router = APIRouter(prefix="/api/v1", tags=["Analytics & Dashboard"])

@router.get("/dashboard", response_model=APIResponse[DashboardStats])
async def get_dashboard_stats():
    now = datetime.now(timezone.utc).isoformat()
    
    total_users = await db.db.users.count_documents({}) if db.db is not None else 0
    total_chats = await db.db.chat_history.count_documents({}) if db.db is not None else 0
    total_documents = await db.db.documents.count_documents({}) if db.db is not None else 0
    total_kb = await db.db.knowledge_base.count_documents({}) if db.db is not None else 0
    
    stats = DashboardStats(
        total_users=total_users,
        total_chats=total_chats,
        total_documents=total_documents,
        total_knowledge_articles=total_kb,
        last_updated=now
    )
    
    return APIResponse(
        success=True,
        message="Dashboard statistics retrieved successfully",
        data=stats
    )

@router.get("/analytics", response_model=APIResponse[AnalyticsDetail])
async def get_analytics_detail(current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    
    total_users = await db.db.users.count_documents({})
    total_chats = await db.db.chat_history.count_documents({})
    total_documents = await db.db.documents.count_documents({})
    total_kb = await db.db.knowledge_base.count_documents({})
    
    # Calculate category distribution in Knowledge Base
    pipeline = [
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_dist = {}
    async for row in db.db.knowledge_base.aggregate(pipeline):
        category = row["_id"] if row["_id"] else "General"
        category_dist[category] = row["count"]
        
    summary = DashboardStats(
        total_users=total_users,
        total_chats=total_chats,
        total_documents=total_documents,
        total_knowledge_articles=total_kb,
        last_updated=now
    )
    
    detail = AnalyticsDetail(
        summary=summary,
        recent_chats_count=total_chats,
        recent_documents_count=total_documents,
        category_distribution=category_dist
    )
    
    return APIResponse(
        success=True,
        message="Detailed analytics retrieved successfully",
        data=detail
    )
