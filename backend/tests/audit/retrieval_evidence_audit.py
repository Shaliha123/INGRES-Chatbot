import asyncio
import json
import logging
from backend.app.config import settings
from backend.app.database import db, connect_to_mongo
from backend.app.services.ai_service import search_relevant_knowledge, normalize_query
import re

async def run_evidence_audit():
    await connect_to_mongo()
    
    query = "List all states that have groundwater data."
    print("=== RETRIEVAL EVIDENCE AUDIT ===")
    print(f"Query: {query}")
    
    clean_q = normalize_query(query)
    keywords = [k for k in re.findall(r'\w+', clean_q) if len(k) > 2]
    regex_pattern = "|".join(keywords) if keywords else clean_q
    
    print("\n1. MongoDB Query Constructed:")
    mongo_query = {
        "$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"content": {"$regex": regex_pattern, "$options": "i"}},
            {"category": {"$regex": regex_pattern, "$options": "i"}},
            {"keywords": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }
    print(json.dumps(mongo_query, indent=2))
    
    print("\n2. Executing Knowledge Base Search...")
    cursor = db.db.knowledge_base.find(mongo_query).limit(4)
    kb_results = await cursor.to_list(length=4)
    print(f"Matched {len(kb_results)} documents in knowledge_base.")
    for doc in kb_results:
        print(f" - Title: {doc.get('title')}, Chunk ID / ID: {doc.get('_id')}")
        
    print("\n3. Executing Documents Collection Search...")
    doc_query = {
        "$or": [
            {"title": {"$regex": regex_pattern, "$options": "i"}},
            {"extracted_text": {"$regex": regex_pattern, "$options": "i"}}
        ]
    }
    limit_remaining = 4 - len(kb_results)
    doc_results = []
    if limit_remaining > 0:
        cursor2 = db.db.documents.find(doc_query).limit(limit_remaining)
        doc_results = await cursor2.to_list(length=limit_remaining)
        print(f"Matched {len(doc_results)} documents in documents collection.")
        for doc in doc_results:
            print(f" - Title: {doc.get('title', doc.get('filename'))}, Chunk ID / ID: {doc.get('_id')}")
    else:
        print("Skipped (limit reached)")
        
    print("\n4. Final Retrieved Context Passed to LLM:")
    context, sources = await search_relevant_knowledge(query, limit=4)
    with open("context_dump.txt", "w", encoding="utf-8") as f:
        f.write(context)
    print("Context successfully written to context_dump.txt")

if __name__ == "__main__":
    asyncio.run(run_evidence_audit())
