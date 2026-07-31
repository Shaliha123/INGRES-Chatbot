import asyncio
from backend.app.database import db, connect_to_mongo, close_mongo_connection
async def count():
    await connect_to_mongo()
    count = await db.db.document_chunks.count_documents({})
    print("Chunks:", count)
    await close_mongo_connection()
if __name__ == "__main__":
    asyncio.run(count())
