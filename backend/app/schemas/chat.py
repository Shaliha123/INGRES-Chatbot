from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChatMessageRequest(BaseModel):
    question: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: str
    conversation_id: str
    question: str
    response: str
    sources_used: List[str]
    intent: Optional[str] = "GENERAL"
    location_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    water_quality_data: Optional[Dict[str, Any]] = None
    groundwater_records: Optional[List[Dict[str, Any]]] = None
    timestamp: str

class ChatHistoryItem(BaseModel):
    id: str
    conversation_id: str
    question: str
    response: str
    sources_used: Optional[List[str]] = []
    intent: Optional[str] = "GENERAL"
    location_data: Optional[Dict[str, Any]] = None
    weather_data: Optional[Dict[str, Any]] = None
    water_quality_data: Optional[Dict[str, Any]] = None
    groundwater_records: Optional[List[Dict[str, Any]]] = None
    timestamp: str
