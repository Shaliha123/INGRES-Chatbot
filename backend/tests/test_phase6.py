import asyncio
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.main import app

async def _test():
    await connect_to_mongo()
    
    # Register test admin user
    await db.db.users.delete_many({"email": "admin_p6@ingres.gov.in"})
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Register Admin
        res_admin = await client.post("/api/v1/register", json={
            "name": "Phase 6 Admin",
            "email": "admin_p6@ingres.gov.in",
            "password": "AdminPassword123!",
            "role": "Admin"
        })
        assert res_admin.status_code == 200
        auth_token = res_admin.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # 1. Test Dashboard Stats Endpoint
        res_dash = await client.get("/api/v1/dashboard")
        assert res_dash.status_code == 200
        dash_data = res_dash.json()["data"]
        assert "total_users" in dash_data
        assert "total_chats" in dash_data
        assert "total_documents" in dash_data
        
        # 2. Test Detailed Analytics Endpoint
        res_analytics = await client.get("/api/v1/analytics", headers=headers)
        assert res_analytics.status_code == 200
        analytics_data = res_analytics.json()["data"]
        assert "category_distribution" in analytics_data
        
        # 3. Test Settings Router
        res_set = await client.get("/api/v1/settings", headers=headers)
        assert res_set.status_code == 200
        set_data = res_set.json()["data"]
        assert set_data["theme"] == "dark"
        
        # Update settings
        res_update_set = await client.put("/api/v1/settings", json={
            "theme": "light",
            "language": "hi",
            "notifications": False
        }, headers=headers)
        assert res_update_set.status_code == 200
        updated_set = res_update_set.json()["data"]
        assert updated_set["theme"] == "light"
        assert updated_set["language"] == "hi"
        
        # 4. Test System Logs Endpoint
        res_logs = await client.get("/api/v1/admin/logs", headers=headers)
        assert res_logs.status_code == 200
        logs = res_logs.json()["data"]
        assert len(logs) >= 1

    # Cleanup
    await db.db.users.delete_many({"email": "admin_p6@ingres.gov.in"})

    await close_mongo_connection()
    print("Phase 6 Analytics, Settings, Admin Dashboard & Logging Verification PASSED!")

if __name__ == "__main__":
    asyncio.run(_test())
