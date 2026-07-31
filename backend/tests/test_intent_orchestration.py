import asyncio
from backend.app.services.intent_service import classify_intent, extract_hydro_entities, orchestrate_intent_workflow
from backend.app.routers.documents import extract_groundwater_measurements

async def main():
    print("==================================================")
    print("INGRES INTENT ORCHESTRATION & ENTITY TEST SUITE")
    print("==================================================")

    # 1. Test Entity Extraction & Generic Word Blacklist
    print("\n1. Testing Entity Extraction & Blacklist:")
    ent_place = extract_hydro_entities("Show groundwater status near place")
    assert ent_place is None, "Generic word 'place' must NOT be extracted as location entity!"
    print("   [OK] Generic word 'place' correctly ignored (no geocoding).")

    ent_loc = extract_hydro_entities("Show groundwater status near location")
    assert ent_loc is None, "Generic word 'location' must NOT be extracted as location entity!"
    print("   [OK] Generic word 'location' correctly ignored.")

    ent_salem = extract_hydro_entities("Water table level in Salem district")
    assert ent_salem is not None and ent_salem["name"] == "Salem", "Salem district must be extracted!"
    print(f"   [OK] Verified district entity extracted: {ent_salem['name']} (Type: {ent_salem['type']})")

    ent_cauvery = extract_hydro_entities("Water level in Cauvery river")
    assert ent_cauvery is not None and ent_cauvery["name"] == "Cauvery", "Cauvery river must be extracted!"
    print(f"   [OK] Verified river entity extracted: {ent_cauvery['name']} (Type: {ent_cauvery['type']})")

    # 2. Test Intent Classification Across 6 Categories
    print("\n2. Testing Intent Classification:")
    assert classify_intent("What is an aquifer?")[0] == "GENERAL"
    print("   [OK] GENERAL intent classified.")

    assert classify_intent("Will rainfall improve groundwater recharge in Chennai this week?")[0] == "WEATHER"
    print("   [OK] WEATHER intent classified.")

    assert classify_intent("Water quality parameters in Salem")[0] == "WATER_QUALITY"
    print("   [OK] WATER_QUALITY intent classified.")

    assert classify_intent("Show groundwater status near Vellore")[0] == "LOCATION"
    print("   [OK] LOCATION intent classified.")

    assert classify_intent("What does the CGWB report say about Coimbatore?")[0] == "DOCUMENT"
    print("   [OK] DOCUMENT intent classified.")

    assert classify_intent("Show system usage analytics and total chats")[0] == "ANALYTICS"
    print("   [OK] ANALYTICS intent classified.")

    # 3. Test Selective API Invocation
    print("\n3. Testing Selective API Invocation:")
    res_generic = await orchestrate_intent_workflow("Show groundwater status near place")
    assert res_generic["location_data"] is None, "Location data must be None when generic word is used!"
    print("   [OK] Nominatim API skipped for generic prompt.")

    res_weather = await orchestrate_intent_workflow("Will rainfall improve groundwater recharge in Chennai this week?")
    assert res_weather["weather_data"] is not None, "Weather data must be present for WEATHER intent!"
    assert res_weather["location_data"] is not None, "Location data must be present for named city!"
    print("   [OK] Open-Meteo & Nominatim selectively invoked for weather prompt.")

    # 4. Test Structured Groundwater Measurement Extractor
    print("\n4. Testing Structured Measurement Extractor:")
    sample_text = "Salem district recorded depth to water level of 14.2 m bgl in November 2026."
    records = extract_groundwater_measurements(sample_text, "test_report.pdf")
    assert len(records) > 0
    assert records[0]["district"] == "Salem"
    assert records[0]["depth_m_bgl"] == 14.2
    assert records[0]["season"] == "Post-Monsoon"
    print(f"   [OK] Parsed structured measurement: District={records[0]['district']}, Depth={records[0]['depth_m_bgl']} m bgl, Season={records[0]['season']}")

    # 5. Test Generative AI Response & Token Optimization Fallback
    print("\n5. Testing Generative AI Response & Token Budgeting:")
    from backend.app.services.ai_service import generate_gemini_response
    gen_ans = await generate_gemini_response("Is groundwater safe to drink in Salem?", res_weather["merged_context"])
    assert len(gen_ans) > 30, "Generative AI response must generate a detailed expert answer!"
    print("   [OK] Generative AI expert response generated successfully!")

    print("\n==================================================")
    print("ALL ORCHESTRATION & RAG INTEGRATION TESTS PASSED!")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
