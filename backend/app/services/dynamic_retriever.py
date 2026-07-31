import logging
import asyncio
from typing import Dict, Any, List, Tuple
from backend.app.services.capability_planner import CapabilityPlan
from backend.app.services.external_api_service import get_coordinates_from_nominatim, get_weather_forecast
from backend.app.services.ai_service import search_relevant_knowledge

logger = logging.getLogger("ingres.retriever")

async def execute_dynamic_retrieval(query: str, plan: CapabilityPlan) -> Dict[str, Any]:
    """
    Dynamic Parallel Multi-Source Retriever:
    Executes targeted data retrieval based on CapabilityPlan without hardcoded routing.
    """
    location_data = None
    weather_data = None
    water_quality_data = None
    sources_used = []
    context_blocks = []

    # 1. Parallel Task Execution: Geocoding & Maps Capability
    if plan.maps and plan.entities:
        target_entity = plan.entities[0]
        location_data = await get_coordinates_from_nominatim(target_entity)

    # 2. Weather Capability
    if plan.weather:
        lat = location_data.get("latitude", 13.0827) if location_data else 13.0827
        lon = location_data.get("longitude", 80.2707) if location_data else 80.2707
        weather_data = await get_weather_forecast(lat, lon)
        if weather_data:
            context_blocks.append(
                f"--- Live Open-Meteo Weather Data ({location_data.get('name', 'Region') if location_data else 'Regional'}) ---\n"
                f"Condition: {weather_data.get('weather_condition')}, Temp: {weather_data.get('temperature')}°C, "
                f"Humidity: {weather_data.get('humidity')}%, 7-Day Rain: {weather_data.get('total_7day_rain_mm')} mm\n"
            )

    # 3. Water Quality Capability
    if plan.water_quality:
        loc_name = plan.entities[0] if plan.entities else "Regional Station"
        from backend.app.database import db
        if db.db is not None:
            record = await db.db.groundwater_records.find_one(
                {"district": {"$regex": f"^{loc_name}$", "$options": "i"}},
                sort=[("year", -1)]
            )
            if record:
                if "_id" in record:
                    record["_id"] = str(record["_id"])
                water_quality_data = record
                context_blocks.append(
                    f"--- Official Water Quality Parameters ({loc_name}) ---\n"
                    f"pH: {record.get('ph', 'N/A')}, TDS: {record.get('tds', 'N/A')} mg/L, Fluoride: {record.get('fluoride', 'N/A')} mg/L\n"
                )

    # 4. RAG Knowledge & Document Vector Retrieval
    if plan.documents or plan.groundwater_database:
        rag_context, rag_sources = await search_relevant_knowledge(query)
        if rag_context:
            context_blocks.append(rag_context)
            sources_used.extend(rag_sources)

    merged_context = "\n\n".join(context_blocks)

    return {
        "location_data": location_data,
        "weather_data": weather_data,
        "water_quality_data": water_quality_data,
        "merged_context": merged_context,
        "sources_used": list(dict.fromkeys(sources_used))
    }
