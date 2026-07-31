from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_users: int
    total_chats: int
    total_documents: int
    total_knowledge_articles: int
    last_updated: str

class AnalyticsDetail(BaseModel):
    summary: DashboardStats
    recent_chats_count: int
    recent_documents_count: int
    category_distribution: Dict[str, int]
    intent_distribution: Dict[str, int]
    weekly_activity: Dict[str, int]
    chunk_count: int
