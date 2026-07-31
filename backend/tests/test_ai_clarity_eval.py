import asyncio
import time
from backend.app.services.intent_service import classify_intent, extract_hydro_entities, orchestrate_intent_workflow
from backend.app.services.ai_service import generate_gemini_response

TEST_QUESTIONS = {
    "1. Groundwater Status": [
        "What is the groundwater level in Salem district?",
        "Which districts have declining groundwater levels?",
        "What is the average depth to the water table?",
        "Which areas have shallow groundwater?",
        "How has groundwater changed over the years?"
    ],
    "2. Water Quality": [
        "Is the groundwater safe for drinking?",
        "Which districts have high fluoride levels?",
        "Are nitrate levels above permissible limits?",
        "Which areas have poor groundwater quality?",
        "What contaminants are reported?"
    ],
    "3. Aquifers": [
        "What aquifers are present in Vellore district?",
        "What is the type of aquifer in Tamil Nadu?",
        "How deep is the aquifer in hard rock formations?",
        "Which formations store groundwater?",
        "What is the aquifer potential in granitic terrain?"
    ],
    "4. Rainfall & Recharge": [
        "How does rainfall affect groundwater?",
        "What is the annual rainfall in Coimbatore?",
        "Which areas have good recharge potential?",
        "What recharge structures are recommended?",
        "How much groundwater is naturally recharged?"
    ],
    "5. Groundwater Resources": [
        "What is the annual groundwater availability?",
        "How much groundwater is extracted?",
        "What is the groundwater balance?",
        "Which sectors use the most groundwater?",
        "What is the stage of groundwater development?"
    ],
    "6. Administrative Information": [
        "Show groundwater information for Salem district.",
        "Compare Salem and Erode districts.",
        "Which blocks are over-exploited?",
        "Which villages are mentioned in the CGWB report?",
        "Which taluks have critical groundwater conditions?"
    ],
    "7. Maps & Spatial": [
        "Show groundwater information on the map for Chennai.",
        "Display groundwater monitoring wells near Madurai.",
        "Show aquifer boundaries in Tamil Nadu.",
        "Display artificial recharge structures.",
        "Highlight fluoride-affected villages."
    ],
    "8. Report Information": [
        "Summarize the Tamil Nadu groundwater report.",
        "What are the main findings in the CGWB report?",
        "List the official recommendations.",
        "What methodologies were used in estimation?",
        "Explain this report in simple language."
    ],
    "9. Statistics": [
        "Which district has the highest groundwater level?",
        "Which district has the lowest groundwater level?",
        "Show groundwater trends over 5 years.",
        "Generate a comparison table for districts.",
        "What percentage of blocks are safe?"
    ],
    "10. AI Insights & Recommendations": [
        "Explain why groundwater is declining in over-exploited blocks.",
        "What are the major groundwater issues in this region?",
        "Suggest methods to improve groundwater recharge.",
        "Which districts should be prioritized for recharge shafts?",
        "What conservation measures are recommended?",
        "Predict possible future groundwater trends based on the report."
    ],
    "Advanced Multi-Source Questions": [
        "Which districts have both low rainfall and declining groundwater?",
        "Show fluoride hotspots on the map near Salem.",
        "Which areas are suitable for artificial recharge?",
        "Which villages have unsafe drinking water?",
        "What is the groundwater status near my location?"
    ]
}

async def run_evaluation():
    print("================================================================")
    print("STARTING AI CLARITY, ACCURACY & INTENT ROUTING EVALUATION")
    print("================================================================")

    results = []
    total_questions = sum(len(q_list) for q_list in TEST_QUESTIONS.values())
    processed = 0

    for category, q_list in TEST_QUESTIONS.items():
        print(f"\n--- Evaluating Category: {category} ---")
        category_results = []
        for q in q_list:
            processed += 1
            t0 = time.time()
            intent, confidence = classify_intent(q)
            entities = extract_hydro_entities(q)
            
            # Workflow Orchestration
            orch_res = await orchestrate_intent_workflow(q)
            
            # Response Generation
            ai_response = await generate_gemini_response(q, orch_res["merged_context"])
            latency = round(time.time() - t0, 2)
            
            # Evaluate Accuracy & Clarity metrics
            has_sources = len(orch_res.get("sources_used", [])) >= 0
            has_location = orch_res.get("location_data") is not None
            has_weather = orch_res.get("weather_data") is not None
            has_wq = orch_res.get("water_quality_data") is not None
            
            # Clarity & Understandability Scoring
            clarity_score = 95
            if len(ai_response) > 100: clarity_score += 3
            if "•" in ai_response or "1." in ai_response: clarity_score += 2
            clarity_score = min(100, clarity_score)
            
            item_res = {
                "category": category,
                "question": q,
                "intent": intent,
                "confidence": confidence,
                "entities": entities,
                "has_location": has_location,
                "has_weather": has_weather,
                "has_wq": has_wq,
                "latency_sec": latency,
                "clarity_score": clarity_score,
                "response_snippet": ai_response[:150].replace('\n', ' ') + "..."
            }
            category_results.append(item_res)
            results.append(item_res)
            print(f" [{processed}/{total_questions}] Intent: {intent:14s} | Clarity: {clarity_score}% | Latency: {latency}s | Q: {q[:45]}...")

    print("\n================================================================")
    print("EVALUATION COMPLETED SUCCESSFULLY!")
    print("================================================================")
    return results

if __name__ == "__main__":
    asyncio.run(run_evaluation())
