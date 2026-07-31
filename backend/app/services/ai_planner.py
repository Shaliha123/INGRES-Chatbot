import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

logger = logging.getLogger("ingres.ai_planner")

class ObjectiveNeed(BaseModel):
    need_groundwater_trends: bool = False
    need_rainfall_forecast: bool = False
    need_district_statistics: bool = False
    need_water_quality: bool = False
    need_spatial_map: bool = False
    need_report_summary: bool = False
    need_structured_data: bool = False
    need_reasoning: bool = True
    need_comparison: bool = False

class StructuredQueryDef(BaseModel):
    intent: str
    entity: str
    operation: str

class AIPlan(BaseModel):
    user_objective: str
    sub_tasks: List[str]
    evidence_required: List[str]
    needs: ObjectiveNeed
    entities: List[str]
    structured_queries: List[StructuredQueryDef] = []
    is_ambiguous: bool = False
    clarification_prompt: Optional[str] = None
from backend.app.schemas.conversation import ConversationContext

def analyze_user_objective(query: str, context: Optional[ConversationContext] = None) -> AIPlan:
    """
    State-of-the-Art AI Reasoning Planner:
    Analyzes the user's true objective, breaks complex queries into sub-tasks,
    and identifies required evidence rather than blindly calling hardcoded APIs.
    """
    from backend.app.services.ai_service import normalize_query
    clean_q = query.strip()
    lower_q = normalize_query(clean_q)
    
    # 1. Fetch Dynamic Entities
    from backend.app.services.intent_service import KNOWN_STATES, KNOWN_DISTRICTS, KNOWN_RIVERS
    
    # 2. Extract Entities
    entities = [d.title() for d in KNOWN_DISTRICTS if d in lower_q]
    entities.extend([s.title() for s in KNOWN_STATES if s in lower_q])
    entities.extend([r.title() for r in KNOWN_RIVERS if r in lower_q])
    entities = list(set(entities))
    # 3. Deterministic Coreference Resolution is handled by ConversationManager
    # The planner just consumes the resolved query and context
    previous_state = context.conversation_state if context else None
    
    # 4. Check Context for Inherited Information
    is_follow_up = "what about" in lower_q or "how about" in lower_q or "compare" in lower_q
    inherited_topic = previous_state.current_topic.lower() if previous_state and previous_state.current_topic != "GENERAL" else ""

    # Clarification Check (Removed bypass, let Gemini ask for clarification if needed)
    is_ambiguous = False
    clarification_msg = None

    # Structured query detection
    structured_queries = []
    need_structured = False
    
    if any(k in lower_q for k in ["list all states", "states that have", "available states"]):
        structured_queries.append(StructuredQueryDef(intent="structured_lookup", entity="state", operation="distinct"))
        need_structured = True
    
    if any(k in lower_q for k in ["list all districts", "which districts", "available districts"]):
        structured_queries.append(StructuredQueryDef(intent="structured_lookup", entity="district", operation="distinct"))
        need_structured = True
        
    if any(k in lower_q for k in ["count", "how many"]):
        if "state" in lower_q:
            structured_queries.append(StructuredQueryDef(intent="structured_lookup", entity="state", operation="count_distinct"))
            need_structured = True
        elif "district" in lower_q:
            structured_queries.append(StructuredQueryDef(intent="structured_lookup", entity="district", operation="count_distinct"))
            need_structured = True
        elif "record" in lower_q or "station" in lower_q:
            structured_queries.append(StructuredQueryDef(intent="structured_lookup", entity="record", operation="count"))
            need_structured = True

    is_district_list = any(k in lower_q for k in ["district", "distrct", "list", "available", "details of", "which districts", "all districts", "tamil nadu"])

    # Identify evidence needs
    needs = ObjectiveNeed(
        need_groundwater_trends=any(k in lower_q + inherited_topic for k in ["declining", "trend", "water level", "table", "depth", "status", "stage", "over-exploited"]) or is_district_list,
        need_rainfall_forecast=any(k in lower_q + inherited_topic for k in ["rain", "rainfall", "weather", "monsoon", "forecast", "precipitation"]),
        need_district_statistics=is_district_list or any(k in lower_q + inherited_topic for k in ["district", "compare", "highest", "lowest", "total", "statistic", "average"]),
        need_water_quality=any(k in lower_q + inherited_topic for k in ["quality", "tds", "fluoride", "nitrate", "ph", "safe", "drinking"]),
        need_spatial_map=any(k in lower_q + inherited_topic for k in ["map", "location", "near", "where", "coordinates", "pin", "wells"]),
        need_report_summary=any(k in lower_q + inherited_topic for k in ["report", "cgwb", "pdf", "findings", "recommendation", "summarize", "summarise"]),
        need_structured_data=need_structured,
        need_comparison=any(k in lower_q for k in ["compare", "versus", "vs", "difference"]) or len(entities) > 1
    )

    # Sub-task decomposition
    sub_tasks = []
    evidence_req = []

    if needs.need_groundwater_trends:
        sub_tasks.append("Retrieve 10-year groundwater level trends and extraction stage")
        evidence_req.append("groundwater_level_trends")
    if needs.need_rainfall_forecast:
        sub_tasks.append("Fetch 7-day precipitation forecast and soil moisture impact")
        evidence_req.append("rainfall_forecast_data")
    if needs.need_water_quality:
        sub_tasks.append("Fetch drinking water compliance metrics (pH, TDS, Fluoride, Nitrate)")
        evidence_req.append("water_quality_parameters")
    if needs.need_spatial_map and entities:
        sub_tasks.append(f"Geocode spatial coordinates for {', '.join(entities)}")
        evidence_req.append("spatial_map_coordinates")
    if needs.need_report_summary and not needs.need_structured_data:
        sub_tasks.append("Search vector indexed CGWB PDF technical reports")
        evidence_req.append("pdf_document_chunks")
        
    if needs.need_structured_data:
        sub_tasks.append("Execute structured database queries")
        evidence_req.append("structured_data")

    if not sub_tasks:
        sub_tasks.append("Perform general hydrogeological reasoning over groundwater knowledge base")
        evidence_req.append("general_knowledge_base")

    plan = AIPlan(
        user_objective=f"Answer hydrogeological query: '{query}'",
        sub_tasks=sub_tasks,
        evidence_required=evidence_req,
        needs=needs,
        entities=entities,
        structured_queries=structured_queries,
        is_ambiguous=is_ambiguous,
        clarification_prompt=clarification_msg
    )

    logger.info(f"AI Planner initialized for query '{query}': {plan.dict()}")
    return plan
