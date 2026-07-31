import asyncio
from backend.app.database import connect_to_mongo, db

async def cleanup():
    await connect_to_mongo()
    print("==================================================")
    print("STARTING DATABASE DEDUPLICATION CLEANUP")
    print("==================================================")

    # 1. Clean up duplicate knowledge_base entries
    kb_docs = await db.db.knowledge_base.find().to_list(500)
    seen_sources = set()
    removed_kb = 0

    for doc in kb_docs:
        source_key = doc.get("source", "")
        title_key = doc.get("title", "")
        unique_key = f"{source_key}::{title_key}"
        
        if unique_key in seen_sources:
            await db.db.knowledge_base.delete_one({"_id": doc["_id"]})
            removed_kb += 1
        else:
            seen_sources.add(unique_key)

    print(f"[OK] Cleaned up {removed_kb} duplicate Knowledge Base entries.")

    # 2. Clean up duplicate documents
    documents = await db.db.documents.find().to_list(500)
    seen_files = set()
    removed_docs = 0

    for doc in documents:
        file_key = f"{doc.get('uploaded_by')}::{doc.get('filename')}"
        if file_key in seen_files:
            await db.db.documents.delete_one({"_id": doc["_id"]})
            removed_docs += 1
        else:
            seen_files.add(file_key)

    print(f"[OK] Cleaned up {removed_docs} duplicate Document records.")

    # 3. Final counts
    remaining_kb = await db.db.knowledge_base.count_documents({})
    remaining_docs = await db.db.documents.count_documents({})
    print("==================================================")
    print(f"CLEANUP COMPLETED! Remaining Unique KB Articles: {remaining_kb}, Documents: {remaining_docs}")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(cleanup())
