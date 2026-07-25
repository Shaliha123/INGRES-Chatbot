from typing import Optional, List
from pydantic import BaseModel, Field

class KnowledgeCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    category: str = Field(..., min_length=2, max_length=100)
    content: str = Field(..., min_length=5)
    keywords: List[str] = Field(default_factory=list)
    source: Optional[str] = "INGRES Portal"

class KnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    keywords: Optional[List[str]] = None
    source: Optional[str] = None

class KnowledgeResponse(BaseModel):
    id: str
    title: str
    category: str
    content: str
    keywords: List[str]
    source: str
    created_at: str
    updated_at: str
