import asyncio
from backend.app.database import connect_to_mongo, db
from backend.app.services.ai_service import search_relevant_knowledge

async def check():
    await connect_to_mongo()
    print("==================================================")
    print("1. CHECKING UPLOADED DOCUMENTS IN MONGODB ATLAS")
    print("==================================================")
    docs = await db.db.documents.find().to_list(100)
    print(f"Total Uploaded Documents: {len(docs)}")
    for d in docs:
        print(f"\n- Filename: {d.get('filename')}")
        print(f"  Title: {d.get('title')}")
        print(f"  Type: {d.get('file_type')}")
        print(f"  Size: {d.get('file_size_bytes')} bytes")
        print(f"  Uploaded By: {d.get('uploaded_by')}")
        text = d.get('extracted_text', '')
        print(f"  Extracted Text Length: {len(text)} characters")
        print(f"  Preview: {repr(text[:200])}")
        
    print("\n==================================================")
    print("2. CHECKING KNOWLEDGE BASE ARTICLES FOR RAG")
    print("==================================================")
    kb = await db.db.knowledge_base.find().to_list(100)
    print(f"Total Knowledge Base Articles: {len(kb)}")
    for k in kb:
        print(f"- Title: {k.get('title')} | Category: {k.get('category')} | Source: {k.get('source')}")

    print("\n==================================================")
    print("3. TESTING RAG SEARCH INTEGRATION")
    print("==================================================")
    sample_query = "groundwater aquifer water"
    retrieved_text, sources = await search_relevant_knowledge(sample_query)
    print(f"Retrieved Context length: {len(retrieved_text)} characters")
    print(f"Sources cited: {sources}")
    print(f"Context Preview:\n{retrieved_text[:400]}")

if __name__ == "__main__":
    asyncio.run(check())

