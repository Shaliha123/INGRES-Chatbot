import asyncio
import time
from backend.app.database import connect_to_mongo, db
from backend.app.services.ai_service import search_relevant_knowledge, generate_gemini_response

async def test_full_rag_pipeline():
    await connect_to_mongo()
    print("======================================================================")
    print("STARTING FULL RAG PIPELINE & AI INTEGRATION VERIFICATION")
    print("======================================================================")

    test_queries = [
        "What is the groundwater year book of Tamil Nadu and Puducherry?",
        "Rainwater harvesting in Salem district",
        "Aquifer recharge rate in Rajasthan sub-basin",
        "Groundwater quality and salinity monitoring parameters"
    ]

    results = []

    for i, query in enumerate(test_queries, 1):
        start_time = time.time()
        print(f"\n--- [Scenario {i}] Query: \"{query}\" ---")
        
        # 1. Test Context Retrieval
        ctx, sources = await search_relevant_knowledge(query)
        retrieval_time = round((time.time() - start_time) * 1000, 2)
        print(f"Retrieval Time: {retrieval_time} ms")
        print(f"Sources Found ({len(sources)}): {sources}")
        
        # 2. Test AI Generation
        gen_start = time.time()
        response = await generate_gemini_response(query, ctx)
        generation_time = round((time.time() - gen_start) * 1000, 2)
        print(f"AI Generation Time: {generation_time} ms")
        print("Response Preview:\n", response[:250], "...\n")

        # 3. Accuracy & Relevance Score Calculation
        keywords_in_query = [k.lower() for k in query.split() if len(k) > 3]
        matches = [k for k in keywords_in_query if k in response.lower() or any(k in s.lower() for s in sources)]
        relevance_score = round((len(matches) / max(len(keywords_in_query), 1)) * 100, 1)

        results.append({
            "scenario": i,
            "query": query,
            "sources_count": len(sources),
            "sources": sources,
            "retrieval_ms": retrieval_time,
            "generation_ms": generation_time,
            "relevance_score": min(relevance_score, 100.0),
            "status": "PASS" if len(sources) > 0 or len(response) > 100 else "WARN"
        })

    print("\n======================================================================")
    print("RAG PIPELINE TEST SUMMARY RESULTS")
    print("======================================================================")
    for r in results:
        print(f"Scenario {r['scenario']}: [{r['status']}] '{r['query'][:35]}...' | Sources: {r['sources_count']} | Latency: {r['retrieval_ms']+r['generation_ms']}ms | Accuracy: {r['relevance_score']}%")

if __name__ == "__main__":
    asyncio.run(test_full_rag_pipeline())
