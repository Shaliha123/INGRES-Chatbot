from typing import Optional, List
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
    timestamp: str

class ChatHistoryItem(BaseModel):
    id: str
    conversation_id: str
    question: str
    response: str
    timestamp: str
