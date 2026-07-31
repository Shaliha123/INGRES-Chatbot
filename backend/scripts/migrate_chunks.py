import asyncio
from pathlib import Path
from backend.app.database import db, connect_to_mongo, close_mongo_connection
from backend.app.routers.documents import extract_text_from_file, process_document_chunks

async def migrate():
    await connect_to_mongo()
    
    # clear existing chunks
    await db.db.document_chunks.delete_many({})
    print("Cleared existing document_chunks.")
    
    cursor = db.db.documents.find()
    async for doc in cursor:
        storage_path = doc.get("storage_path")
        file_ext = doc.get("file_type")
        doc_id = str(doc["_id"])
        title = doc.get("title", doc.get("filename"))
        
        if not storage_path or not Path(storage_path).exists():
            print(f"Skipping {title} - storage path not found.")
            continue
            
        print(f"Migrating {title}...")
        pages = extract_text_from_file(Path(storage_path), file_ext)
        await process_document_chunks(pages, doc_id, title)
        print(f"Done migrating {title}.")
        
    print("Migration complete!")
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(migrate())
