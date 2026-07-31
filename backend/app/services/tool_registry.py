import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable
from backend.app.services.external_api_service import get_coordinates_from_nominatim, get_weather_forecast
from backend.app.services.ai_service import search_relevant_knowledge

logger = logging.getLogger("ingres.tools")

class BaseTool:
    name: str
    description: str

    async def execute(self, **kwargs) -> Dict[str, Any]:
        raise NotImplementedError

from backend.app.schemas.conversation import WeatherResult, MapResult, DocumentResult, WaterQualityResult, GroundwaterResult

class WeatherTool(BaseTool):
    name = "weather_tool"
    description = "Fetches 7-day rainfall forecasts and temperature from Open-Meteo API"

    async def execute(self, location_data: Optional[Dict[str, Any]] = None, **kwargs) -> WeatherResult:
        lat = location_data.get("latitude", 13.0827) if location_data else 13.0827
        lon = location_data.get("longitude", 80.2707) if location_data else 80.2707
        data = await get_weather_forecast(lat, lon)
        return WeatherResult(
            success=True,
            confidence=1.0,
            payload=data,
            evidence=[data] if data else [],
            metadata={"source": "Open-Meteo"}
        )

class MapTool(BaseTool):
    name = "map_tool"
    description = "Geocodes location names into spatial coordinates via OpenStreetMap Nominatim"

    async def execute(self, entity_name: str, **kwargs) -> MapResult:
        data = await get_coordinates_from_nominatim(entity_name)
        return MapResult(
            success=True if data else False,
            confidence=0.9,
            payload=data,
            evidence=[data] if data else [],
            metadata={"source": "Nominatim"}
        )

class DocumentTool(BaseTool):
    name = "document_tool"
    description = "Performs hybrid vector & keyword RAG search over indexed PDF reports"

    async def execute(self, query: str, **kwargs) -> DocumentResult:
        context, sources, diagnostics = await search_relevant_knowledge(query)
        return DocumentResult(
            success=True if context else False,
            confidence=0.85,
            payload=context,
            evidence=[context] if context else [],
            metadata={"sources": sources, "diagnostics": diagnostics}
        )

class WaterQualityTool(BaseTool):
    name = "water_quality_tool"
    description = "Retrieves ground water quality parameters against BIS IS:10500 standards"

    async def execute(self, entity_name: str = "Regional Station", **kwargs) -> WaterQualityResult:
        from backend.app.database import db
        if db.db is not None:
            # Check dynamic relationships for hierarchical aggregation (e.g. State -> Districts)
            from backend.app.services.intent_service import KNOWN_STATES
            is_parent = entity_name.lower() in KNOWN_STATES
            
            if is_parent:
                records = await db.db.groundwater_records.find(
                    {"state": {"$regex": f"^{entity_name}$", "$options": "i"}},
                    sort=[("year", -1)]
                ).to_list(15)
                if records:
                    context = [f"--- Water Quality Summary for Region: {entity_name} ---"]
                    for r in records:
                        context.append(f"Child Entity: {r.get('district')}, pH: {r.get('ph', 'N/A')}, TDS: {r.get('tds', 'N/A')} mg/L, Nitrate: {r.get('nitrate', 'N/A')}")
                    return WaterQualityResult(
                        success=True, confidence=1.0, payload=records, evidence=[{"document_context": "\n".join(context)}]
                    )
            else:
                # Query the actual groundwater records for district
                record = await db.db.groundwater_records.find_one(
                    {"district": {"$regex": f"^{entity_name}$", "$options": "i"}},
                    sort=[("year", -1)]
                )
                if record:
                    if "_id" in record:
                        record["_id"] = str(record["_id"])
                    context_str = f"--- Water Quality Data ({entity_name}) ---\npH: {record.get('ph', 'N/A')}, TDS: {record.get('tds', 'N/A')} mg/L, Fluoride: {record.get('fluoride', 'N/A')} mg/L"
                    return WaterQualityResult(
                        success=True, confidence=1.0, payload=record, evidence=[{"document_context": context_str}]
                    )
        return WaterQualityResult(success=False, confidence=0.0)

class StructuredDataTool(BaseTool):
    name = "structured_data_tool"
    description = "Executes structured database queries based on planner intents"
    
    async def execute(self, structured_queries: List[Any], **kwargs) -> GroundwaterResult:
        from backend.app.database import db
        if not db.db:
            return GroundwaterResult(success=False, confidence=0.0)
            
        results = []
        for sq in structured_queries:
            intent = getattr(sq, "intent", sq.get("intent") if isinstance(sq, dict) else None)
            entity = getattr(sq, "entity", sq.get("entity") if isinstance(sq, dict) else None)
            op = getattr(sq, "operation", sq.get("operation") if isinstance(sq, dict) else None)
            
            if intent == "structured_lookup":
                try:
                    if op == "distinct":
                        field = entity if entity else "state"
                        items = await db.db.groundwater_records.distinct(field)
                        results.append(f"List of all {field}s in the database: {', '.join(sorted(items))}")
                    elif op == "count_distinct":
                        field = entity if entity else "state"
                        items = await db.db.groundwater_records.distinct(field)
                        results.append(f"Total number of {field}s with data: {len(items)}")
                    elif op == "count":
                        count = await db.db.groundwater_records.count_documents({})
                        results.append(f"Total groundwater records available: {count}")
                except Exception as e:
                    logger.error(f"StructuredDataTool failed for intent={intent}: {e}")
                    
        return GroundwaterResult(
            success=True if results else False, 
            confidence=1.0, 
            payload=results, 
            evidence=[{"document_context": "\n".join(results)}] if results else []
        )

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.register(WeatherTool())
        self.register(MapTool())
        self.register(DocumentTool())
        self.register(WaterQualityTool())
        self.register(StructuredDataTool())

    def register(self, tool: BaseTool):
        self._tools[tool.name] = tool
        logger.info(f"Registered tool: '{tool.name}'")

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

tool_registry = ToolRegistry()
