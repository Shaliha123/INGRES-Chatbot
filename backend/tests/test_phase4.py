import asyncio
import io
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.main import app

async def _test():
    await connect_to_mongo()
    
    # Register temporary test user for auth headers
    await db.db.users.delete_many({"email": "kb_tester_p4@ingres.gov.in"})
    await db.db.knowledge_base.delete_many({"source": "Phase 4 Test"})
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        res_reg = await client.post("/api/v1/register", json={
            "name": "Phase 4 Tester",
            "email": "kb_tester_p4@ingres.gov.in",
            "password": "Password123!",
            "role": "Admin"
        })
        assert res_reg.status_code == 200
        auth_token = res_reg.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Create Knowledge Base Item
        res_kb = await client.post("/api/v1/knowledge", json={
            "title": "Groundwater Level Monitoring in State of Gujarat",
            "category": "Hydrology Data",
            "content": "The average water table depth in northern Gujarat is 45 meters below ground level as of 2026 assessment.",
            "keywords": ["Gujarat", "Groundwater", "Water Table"],
            "source": "Phase 4 Test"
        }, headers=headers)
        assert res_kb.status_code == 200, res_kb.text
        kb_id = res_kb.json()["data"]["id"]
        
        # 2. Search Knowledge Base
        res_search = await client.get("/api/v1/knowledge?q=Gujarat")
        assert res_search.status_code == 200
        items = res_search.json()["data"]
        assert len(items) >= 1
        assert "Gujarat" in items[0]["title"]
        
        # 3. Upload Text Document
        file_content = b"INGRES Technical Report 2026: Aquifer recharge rate in Rajasthan sub-basin is 12% annually."
        files = {"file": ("test_report_2026.txt", io.BytesIO(file_content), "text/plain")}
        res_doc = await client.post("/api/v1/documents", files=files, data={"title": "Rajasthan Aquifer Report"}, headers=headers)
        assert res_doc.status_code == 200, res_doc.text
        doc_data = res_doc.json()["data"]
        doc_id = doc_data["id"]
        assert "Rajasthan" in doc_data["extracted_text_preview"]
        
        # 4. List Documents
        res_docs_list = await client.get("/api/v1/documents")
        assert res_docs_list.status_code == 200
        assert len(res_docs_list.json()["data"]) >= 1
        
        # 5. Delete test document & knowledge item
        res_del_doc = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
        assert res_del_doc.status_code == 200
        
        res_del_kb = await client.delete(f"/api/v1/knowledge/{kb_id}", headers=headers)
        assert res_del_kb.status_code == 200

    # Cleanup
    await db.db.users.delete_many({"email": "kb_tester_p4@ingres.gov.in"})
    await db.db.knowledge_base.delete_many({"source": "Phase 4 Test"})

    await close_mongo_connection()
    print("Phase 4 Knowledge Base & Document Management Verification PASSED!")

if __name__ == "__main__":
    asyncio.run(_test())
