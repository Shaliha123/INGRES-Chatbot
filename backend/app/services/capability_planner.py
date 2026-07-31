import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("ingres.planner")

class CapabilityPlan(BaseModel):
    documents: bool = False
    groundwater_database: bool = False
    weather: bool = False
    maps: bool = False
    analytics: bool = False
    historical_data: bool = False
    water_quality: bool = False
    comparison: bool = False
    entities: List[str] = []
    keywords: List[str] = []
    reasoning_goal: str = ""

def plan_capabilities(query: str, history: Optional[List[Dict[str, Any]]] = None) -> CapabilityPlan:
    """
    Dynamic AI Capability Planner:
    Replaces static single-intent classification with a multi-capability execution plan.
    Determines dynamically which data services, collections, and tools are needed.
    """
    lower_q = query.lower()
    
    # Capability indicators
    is_weather = any(k in lower_q for k in ["rain", "rainfall", "weather", "monsoon", "climate", "forecast", "precipitation", "temperature"])
    is_wq = any(k in lower_q for k in ["quality", "tds", "fluoride", "nitrate", "ph", "salinity", "contamination", "drinking", "potable"])
    is_map = any(k in lower_q for k in ["map", "location", "near", "where", "coordinates", "pin", "station", "wells near"])
    is_analytics = any(k in lower_q for k in ["analytics", "stat", "total", "count", "average", "highest", "lowest", "trend", "percentage", "compare"])
    is_doc = any(k in lower_q for k in ["report", "cgwb", "document", "pdf", "section", "published", "file", "summarize", "findings", "recommendation"])
    is_gw_status = any(k in lower_q for k in ["groundwater", "water level", "water table", "depth", "declining", "status", "recharge", "aquifer", "over-exploited", "stage"])
    is_comparison = any(k in lower_q for k in ["compare", "versus", "vs", "difference", "between"])
    is_historical = any(k in lower_q for k in ["trend", "history", "years", "historical", "over time", "past", "2020", "2025", "change"])

    # Extract entity candidates
    entities = []
    from backend.app.services.intent_service import KNOWN_DISTRICTS, KNOWN_STATES, KNOWN_RIVERS
    for dist in KNOWN_DISTRICTS:
        if dist in lower_q:
            entities.append(dist.title())
    for st in KNOWN_STATES:
        if st in lower_q:
            entities.append(st.title())
    for riv in KNOWN_RIVERS:
        if riv in lower_q:
            entities.append(riv.title())

    # Build multi-capability activation matrix
    plan = CapabilityPlan(
        documents=is_doc or is_gw_status or (not is_weather and not is_wq),
        groundwater_database=is_gw_status or is_analytics or is_comparison or len(entities) > 0,
        weather=is_weather,
        maps=is_map or len(entities) > 0,
        analytics=is_analytics or is_comparison,
        historical_data=is_historical,
        water_quality=is_wq,
        comparison=is_comparison or len(entities) > 1,
        entities=list(set(entities)),
        keywords=[w for w in lower_q.split() if len(w) > 3],
        reasoning_goal=f"Synthesize hydrogeological analysis for query: '{query}'"
    )

    logger.info(f"Capability Planner generated plan: {plan.dict()}")
    return plan
