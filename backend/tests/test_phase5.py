import asyncio
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.main import app

async def _test():
    await connect_to_mongo()
    
    # Setup test user and test KB record
    await db.db.users.delete_many({"email": "rag_tester_p5@ingres.gov.in"})
    await db.db.knowledge_base.delete_many({"source": "Phase 5 Test RAG"})
    
    # Seed specific groundwater document into Knowledge Base
    kb_entry = {
        "title": "Punjab Groundwater Depletion Status 2026",
        "category": "Regional Aquifers",
        "content": "In central Punjab districts (Sangrur, Patiala, Ludhiana), water table decline averages 0.5 meters per year due to paddy cultivation reliance.",
        "keywords": ["Punjab", "Sangrur", "Patiala", "Ludhiana", "paddy"],
        "source": "Phase 5 Test RAG"
    }
    await db.db.knowledge_base.insert_one(kb_entry)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        res_reg = await client.post("/api/v1/register", json={
            "name": "Phase 5 RAG Tester",
            "email": "rag_tester_p5@ingres.gov.in",
            "password": "Password123!",
            "role": "User"
        })
        assert res_reg.status_code == 200
        auth_token = res_reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Send Chat Question targeting RAG context
        question = "What is the annual water table decline rate in Sangrur and Ludhiana?"
        res_chat = await client.post("/api/v1/chat", json={
            "question": question
        }, headers=headers)
        assert res_chat.status_code == 200, res_chat.text
        chat_data = res_chat.json()["data"]
        assert chat_data["question"] == question
        assert len(chat_data["response"]) > 20
        assert "Punjab Groundwater Depletion Status 2026" in chat_data["sources_used"]
        
        # 2. Verify Chat History Endpoint
        res_hist = await client.get("/api/v1/chat/history", headers=headers)
        assert res_hist.status_code == 200
        history_items = res_hist.json()["data"]
        assert len(history_items) >= 1
        assert history_items[0]["question"] == question

        # 3. Clear Chat History
        res_clear = await client.delete("/api/v1/chat/history", headers=headers)
        assert res_clear.status_code == 200
        assert res_clear.json()["data"]["deleted_count"] >= 1

    # Cleanup
    await db.db.users.delete_many({"email": "rag_tester_p5@ingres.gov.in"})
    await db.db.knowledge_base.delete_many({"source": "Phase 5 Test RAG"})

    await close_mongo_connection()
    print("Phase 5 RAG Pipeline & Gemini AI Chat System Verification PASSED!")

if __name__ == "__main__":
    asyncio.run(_test())
