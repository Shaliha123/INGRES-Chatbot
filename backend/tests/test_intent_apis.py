import asyncio
from backend.app.services.external_api_service import get_coordinates_from_nominatim, get_weather_forecast
from backend.app.services.intent_service import classify_intent, orchestrate_intent_workflow

async def main():
    print("Testing Intent Classification...")
    assert classify_intent("Will rainfall improve groundwater recharge in Chennai this week?")[0] == "WEATHER"
    assert classify_intent("Show groundwater status near Vellore")[0] == "LOCATION"
    assert classify_intent("Water quality parameters in Salem")[0] == "WATER_QUALITY"
    assert classify_intent("What does the CGWB report say about Coimbatore?")[0] == "DOCUMENT"
    assert classify_intent("What is an aquifer?")[0] == "GENERAL"
    print("[OK] Intent Classification Test Passed!")

    print("\nTesting Nominatim Geocoding API...")
    coords = await get_coordinates_from_nominatim("Chennai")
    assert coords is not None
    assert "latitude" in coords and "longitude" in coords
    assert coords["name"] == "Chennai"
    print(f"[OK] Nominatim Geocoding Test Passed! Location: {coords['name']} ({coords['latitude']}, {coords['longitude']})")

    print("\nTesting Open-Meteo Weather API...")
    weather = await get_weather_forecast(coords["latitude"], coords["longitude"])
    assert weather is not None
    assert "temperature" in weather
    assert "total_7day_rain_mm" in weather
    assert len(weather["daily_forecast"]) > 0
    print(f"[OK] Open-Meteo Weather Test Passed! Temp: {weather['temperature']} C, 7-Day Rain: {weather['total_7day_rain_mm']} mm")

    print("\nTesting Intent Workflow Orchestrator...")
    res = await orchestrate_intent_workflow("Will rainfall improve groundwater in Chennai this week?")
    assert res["intent"] == "WEATHER"
    assert res["weather_data"] is not None
    assert res["location_data"] is not None
    print("[OK] Intent Workflow Orchestration Test Passed!")
    print("\nALL INTENT & EXTERNAL API INTEGRATION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(main())
