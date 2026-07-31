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
    
    total_users = await db.db.users.count_documents({}) if db.db is not None else 0
    total_chats = await db.db.chat_history.count_documents({}) if db.db is not None else 0
    total_documents = await db.db.documents.count_documents({}) if db.db is not None else 0
    total_kb = await db.db.knowledge_base.count_documents({}) if db.db is not None else 0
    
    # 1. Exact Chunk Count from document_chunks collection
    chunk_count = 0
    if db.db is not None and "document_chunks" in await db.db.list_collection_names():
        chunk_count = await db.db.document_chunks.count_documents({})
    
    # 2. Exact Knowledge Base Category Aggregation
    category_dist = {}
    if db.db is not None:
        async for row in db.db.knowledge_base.aggregate([{"$group": {"_id": "$category", "count": {"$sum": 1}}}]):
            cat = row["_id"] if row["_id"] else "General"
            category_dist[cat] = row["count"]

    # 3. Exact Intent Breakdown & Real Weekly Activity from chat_history documents
    intent_dist = {"GENERAL": 0, "WEATHER": 0, "WATER_QUALITY": 0, "LOCATION": 0, "DOCUMENT": 0, "ANALYTICS": 0}
    weekly_act = {"Mon": 0, "Tue": 0, "Wed": 0, "Thu": 0, "Fri": 0, "Sat": 0, "Sun": 0}

    if db.db is not None:
        async for chat in db.db.chat_history.find({}):
            # Count exact intent
            intent = chat.get("intent", "GENERAL")
            if intent in intent_dist:
                intent_dist[intent] += 1
            else:
                intent_dist[intent] = 1

            # Count exact day of week from real ISO timestamp
            ts_str = chat.get("timestamp")
            if ts_str:
                try:
                    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    day_name = dt.strftime("%a") # e.g. Mon, Tue, Wed...
                    if day_name in weekly_act:
                        weekly_act[day_name] += 1
                except Exception:
                    pass

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
        category_distribution=category_dist,
        intent_distribution=intent_dist,
        weekly_activity=weekly_act,
        chunk_count=chunk_count
    )
    
    return APIResponse(
        success=True,
        message="Detailed analytics retrieved successfully",
        data=detail
    )
