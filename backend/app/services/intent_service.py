import logging
import re
from typing import Dict, Any, Tuple, Optional, List
from backend.app.services.external_api_service import get_coordinates_from_nominatim, get_weather_forecast
from backend.app.services.ai_service import search_relevant_knowledge

logger = logging.getLogger("ingres.intent")

# Verified Hydrogeological Entity Catalogs
KNOWN_STATES = []
KNOWN_DISTRICTS = []

async def load_dynamic_entities():
    """Dynamically load states and districts from the database."""
    from backend.app.database import db
    global KNOWN_STATES, KNOWN_DISTRICTS
    try:
        if db.db is not None:
            states = await db.db.groundwater_records.distinct("state")
            districts = await db.db.groundwater_records.distinct("district")
            if states:
                KNOWN_STATES.clear()
                KNOWN_STATES.extend([s.lower() for s in states if isinstance(s, str)])
            if districts:
                KNOWN_DISTRICTS.clear()
                KNOWN_DISTRICTS.extend([d.lower() for d in districts if isinstance(d, str)])
            logger.info(f"Loaded {len(KNOWN_STATES)} states and {len(KNOWN_DISTRICTS)} districts from DB.")
    except Exception as e:
        logger.error(f"Failed to load dynamic entities: {e}")


KNOWN_RIVERS = ["cauvery", "kaveri", "vaigai", "palar", "tamiraparani", "bhavani", "amaravathi", "noyyal", "cheyyar"]

KNOWN_AQUIFERS_RESERVOIRS = [
    "mettur", "chembarambakkam", "poondi", "red hills", "cholavaram", "sathanur",
    "charnockite", "alluvial", "sandstone", "hard rock", "crystalline"
]

# Blacklist against generic words to prevent useless geocoding
GENERIC_LOCATION_WORDS = {
    "place", "location", "area", "city", "district", "village", "town", "region",
    "groundwater", "water", "level", "table", "depth", "status", "report", "data",
    "aquifer", "quality", "weather", "rain", "forecast", "state", "wise", "details"
}

def extract_hydro_entities(query: str) -> Optional[Dict[str, str]]:
    """
    Extract specific, verified hydrogeological entities from the prompt.
    Returns None if only generic words are present.
    """
    lower_q = query.lower()

    # 1. State check
    for st in KNOWN_STATES:
        if st in lower_q:
            return {"name": st.title(), "type": "state"}

    # 2. District check
    for dist in KNOWN_DISTRICTS:
        if dist in lower_q:
            return {"name": dist.title(), "type": "district"}

    # 3. River check
    for riv in KNOWN_RIVERS:
        if riv in lower_q:
            return {"name": riv.title(), "type": "river"}

    # 4. Aquifer / Reservoir check
    for aq in KNOWN_AQUIFERS_RESERVOIRS:
        if aq in lower_q:
            return {"name": aq.title(), "type": "aquifer_reservoir"}

    # 5. Preposition pattern match with strict blacklist filter
    loc_match = re.search(r'\b(?:in|near|for|around|at)\s+([A-Za-z]+)', query, re.IGNORECASE)
    if loc_match:
        candidate = loc_match.group(1).lower().strip()
        if len(candidate) >= 3 and candidate not in GENERIC_LOCATION_WORDS:
            return {"name": candidate.title(), "type": "named_place"}

    return None


def classify_intent(query: str) -> Tuple[str, Optional[Dict[str, str]]]:
    """
    Classify query into explicit intents:
    'GENERAL', 'WEATHER', 'WATER_QUALITY', 'LOCATION', 'DOCUMENT', 'ANALYTICS', 'GROUNDWATER_STATUS'
    """
    lower_q = query.lower()
    entity = extract_hydro_entities(query)

    # 1. Analytics Intent
    if any(k in lower_q for k in ["analytics", "system stats", "total chats", "usage metrics", "how many chats", "dashboard stats"]):
        return "ANALYTICS", entity

    # 2. Weather & Rainfall Intent
    if any(k in lower_q for k in ["rain", "rainfall", "weather", "monsoon", "climate", "forecast", "precipitation", "temperature", "cloud"]):
        return "WEATHER", entity

    # 3. Water Quality Intent
    if any(k in lower_q for k in ["quality", "tds", "fluoride", "nitrate", "ph", "salinity", "contamination", "drinking", "potable", "polluted"]):
        return "WATER_QUALITY", entity

    # 4. Specific Groundwater Status / Declining Trends Intent
    if any(k in lower_q for k in ["declining", "increasing", "status", "water level", "water table", "which districts", "over-exploited", "trend", "shallow"]):
        return "GROUNDWATER_STATUS", entity

    # 5. Document / Report Intent
    if any(k in lower_q for k in ["report", "cgwb", "document", "pdf", "section", "published", "file", "uploaded report"]):
        return "DOCUMENT", entity

    # 6. Specific Location Intent
    if entity is not None or any(k in lower_q for k in ["where", "near", "location map", "coordinates", "depth in", "table in"]):
        return "LOCATION", entity

    # 7. General Groundwater Intent
    return "GENERAL", entity



async def orchestrate_intent_workflow(query: str) -> Dict[str, Any]:
    """
    Production-Grade Generative AI Orchestrator Pipeline:
    1. Question Understanding & Dynamic Capability Planning (CapabilityPlanner)
    2. Dynamic Parallel Multi-Source Retrieval (DynamicRetriever)
    3. Context & Metadata Assembly
    """
    from backend.app.services.capability_planner import plan_capabilities
    from backend.app.services.dynamic_retriever import execute_dynamic_retrieval
    from backend.app.services.evidence_validator import validate_retrieved_evidence

    # 1. Capability Planning
    plan = plan_capabilities(query)
    intent, entity = classify_intent(query)
    logger.info(f"Capability Orchestrator: Query='{query}' -> Plan={plan.dict()}")

    # 2. Dynamic Parallel Retrieval
    retrieval_res = await execute_dynamic_retrieval(query, plan)
    
    # 3. Evidence Validation
    validation_res = validate_retrieved_evidence(query, retrieval_res["merged_context"], plan.dict())

    return {
        "intent": intent,
        "entity": entity,
        "capability_plan": plan.dict(),
        "validation": validation_res.dict(),
        "location_data": retrieval_res["location_data"],
        "weather_data": retrieval_res["weather_data"],
        "water_quality_data": retrieval_res["water_quality_data"],
        "merged_context": retrieval_res["merged_context"],
        "sources_used": retrieval_res["sources_used"]
    }
