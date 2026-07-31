import asyncio
import io
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.main import app

async def run_master_e2e_suite():
    print("=" * 70)
    print("STARTING MASTER END-TO-END VERIFICATION SUITE FOR INGRES")
    print("=" * 70)
    
    await connect_to_mongo()
    
    # 0. Clean test environment
    test_emails = ["master_user@ingres.gov.in", "master_admin@ingres.gov.in"]
    await db.db.users.delete_many({"email": {"$in": test_emails}})
    await db.db.knowledge_base.delete_many({"source": "Master E2E Suite"})
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        # Step 1: Health Check
        res = await client.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["data"]["database_connected"] is True
        print("[OK] Step 1: System Health Check Passed")
        
        # Step 2: Register User & Admin
        res_user_reg = await client.post("/api/v1/register", json={
            "name": "E2E Regular User",
            "email": test_emails[0],
            "password": "UserPass123!",
            "role": "User"
        })
        assert res_user_reg.status_code == 200
        user_token = res_user_reg.json()["data"]["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}
        
        res_admin_reg = await client.post("/api/v1/register", json={
            "name": "E2E Admin User",
            "email": test_emails[1],
            "password": "AdminPass123!",
            "role": "Admin"
        })
        assert res_admin_reg.status_code == 200
        admin_token = res_admin_reg.json()["data"]["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        print("[OK] Step 2: User & Admin Registration Passed")
        
        # Step 3: Profile & Auth Middleware
        res_prof = await client.get("/api/v1/profile", headers=user_headers)
        assert res_prof.status_code == 200
        assert res_prof.json()["data"]["email"] == test_emails[0]
        print("[OK] Step 3: Auth & Profile Middleware Passed")
        
        # Step 4: Knowledge Base Operations
        res_kb = await client.post("/api/v1/knowledge", json={
            "title": "Groundwater Salinity Assessment 2026",
            "category": "Water Quality",
            "content": "Salinity levels in coastal Tamil Nadu aquifers range from 1500 to 3200 mg/L TDS.",
            "keywords": ["Tamil Nadu", "Salinity", "TDS", "Aquifer"],
            "source": "Master E2E Suite"
        }, headers=admin_headers)
        assert res_kb.status_code == 200
        kb_id = res_kb.json()["data"]["id"]
        print("[OK] Step 4: Knowledge Base Creation & Ingestion Passed")
        
        # Step 5: Document Upload & Parser
        import time
        test_filename = f"salem_harvesting_{int(time.time())}.txt"
        doc_bytes = b"INGRES Document 2026: Rainwater harvesting structures restored 450 TCM in Salem district."
        files = {"file": (test_filename, io.BytesIO(doc_bytes), "text/plain")}
        res_doc = await client.post("/api/v1/documents", files=files, data={"title": "Salem Rainwater Report"}, headers=user_headers)
        assert res_doc.status_code == 200
        doc_id = res_doc.json()["data"]["id"]
        print("[OK] Step 5: Document Upload & Text Extraction Parser Passed")

        
        # Step 6: RAG Chat Pipeline Execution
        res_chat = await client.post("/api/v1/chat", json={
            "question": "What is the aquifer salinity range in coastal Tamil Nadu?"
        }, headers=user_headers)
        assert res_chat.status_code == 200
        chat_resp = res_chat.json()["data"]
        assert len(chat_resp["response"]) > 20
        assert len(chat_resp["sources_used"]) > 0
        print("[OK] Step 6: RAG Chat & Gemini AI Ingestion Passed")

        
        # Step 7: Settings & Dashboard Metrics
        res_set = await client.put("/api/v1/settings", json={"theme": "dark", "language": "en"}, headers=user_headers)
        assert res_set.status_code == 200
        
        res_dash = await client.get("/api/v1/dashboard")
        assert res_dash.status_code == 200
        assert res_dash.json()["data"]["total_users"] >= 2
        print("[OK] Step 7: Dashboard Metrics & Settings Management Passed")
        
        # Step 8: Admin Audit Logs & User List
        res_logs = await client.get("/api/v1/admin/logs", headers=admin_headers)
        assert res_logs.status_code == 200
        assert len(res_logs.json()["data"]) >= 5
        print("[OK] Step 8: Admin Audit Log Engine Passed")
        
        # Step 9: Cleanup test items
        await client.delete(f"/api/v1/documents/{doc_id}", headers=user_headers)
        await client.delete(f"/api/v1/knowledge/{kb_id}", headers=admin_headers)
        await db.db.users.delete_many({"email": {"$in": test_emails}})
        print("[OK] Step 9: Post-Test Cleanup Completed Successfully")

    await close_mongo_connection()
    print("=" * 70)
    print("MASTER END-TO-END VERIFICATION SUITE PASSED 100% SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(run_master_e2e_suite())
