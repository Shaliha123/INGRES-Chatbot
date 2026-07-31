import sys
import asyncio
from backend.app.database import connect_to_mongo
from backend.app.services.ai_service import search_relevant_knowledge, generate_gemini_response

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

async def test_rag():
    await connect_to_mongo()
    query = "Groundwater level in Tamil Nadu"
    ctx, sources = await search_relevant_knowledge(query)
    response = await generate_gemini_response(query, ctx)
    print("\n" + "="*60)
    print("QUERY:", query)
    print("SOURCES USED:", sources)
    print("="*60)
    print(response)
    print("="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(test_rag())
