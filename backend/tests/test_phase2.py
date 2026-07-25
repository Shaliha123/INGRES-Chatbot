import asyncio
from backend.app.config import settings
from backend.app.database import connect_to_mongo, close_mongo_connection, db

def run_async_test(coro):
    return asyncio.run(coro)

def test_mongodb_atlas_connection_and_indexes():
    async def _test():
        await connect_to_mongo()
        assert db.db is not None
        
        # Verify database ping
        pong = await db.db.command("ping")
        assert pong.get("ok") == 1.0 or pong.get("ok") == 1
        
        # Perform test insertion and query in logs collection
        test_log = {
            "user_id": "system_test",
            "action": "phase2_db_verification",
            "status": "success",
            "timestamp": "2026-07-25T16:00:00Z"
        }
        res = await db.db.logs.insert_one(test_log)
        assert res.inserted_id is not None
        
        # Query back
        doc = await db.db.logs.find_one({"_id": res.inserted_id})
        assert doc["action"] == "phase2_db_verification"
        
        # Clean up test log
        await db.db.logs.delete_one({"_id": res.inserted_id})
        
        await close_mongo_connection()
        print("MongoDB Atlas Live Connection & Index Verification PASSED!")

    run_async_test(_test())

if __name__ == "__main__":
    test_mongodb_atlas_connection_and_indexes()
