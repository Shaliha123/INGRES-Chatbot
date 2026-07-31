from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

class ConversationState(BaseModel):
    conversation_id: str
    current_topic: str = "GENERAL"
    entities: Dict[str, str] = Field(default_factory=dict)
    active_document: Optional[str] = None
    active_report: Optional[str] = None
    active_sources: List[str] = Field(default_factory=list)
    last_tool: Optional[str] = None
    last_intent: Optional[str] = None
    retrieval_metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ConversationContext(BaseModel):
    history: List[Dict[str, Any]] = Field(default_factory=list)
    conversation_state: ConversationState
    current_topic: str = "GENERAL"
    entities: Dict[str, str] = Field(default_factory=dict)
    retrieved_documents: List[str] = Field(default_factory=list)
    active_sources: List[str] = Field(default_factory=list)
    active_tools: List[str] = Field(default_factory=list)

class ToolResult(BaseModel):
    tool_name: str
    success: bool
    confidence: float
    evidence: List[Any] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    payload: Any = None

class GroundwaterResult(ToolResult):
    tool_name: str = "structured_data_tool"

class WeatherResult(ToolResult):
    tool_name: str = "weather_tool"

class DocumentResult(ToolResult):
    tool_name: str = "document_tool"

class MapResult(ToolResult):
    tool_name: str = "map_tool"

class WaterQualityResult(ToolResult):
    tool_name: str = "water_quality_tool"
