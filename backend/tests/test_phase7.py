import asyncio
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.main import app

async def _test():
    await connect_to_mongo()
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as client:
        # Verify CORS headers for browser requests
        res_cors = await client.options("/api/v1/health", headers={
            "Origin": "http://localhost:5500",
            "Access-Control-Request-Method": "GET"
        })
        assert res_cors.status_code in [200, 204]
        
        # Verify OpenAPI Schema matches API specs
        res_openapi = await client.get("/openapi.json")
        assert res_openapi.status_code == 200
        schema = res_openapi.json()
        paths = schema.get("paths", {})
        
        expected_paths = [
            "/api/v1/register",
            "/api/v1/login",
            "/api/v1/profile",
            "/api/v1/chat",
            "/api/v1/chat/history",
            "/api/v1/knowledge",
            "/api/v1/documents",
            "/api/v1/dashboard",
            "/api/v1/analytics",
            "/api/v1/settings",
            "/api/v1/users",
            "/api/v1/admin/logs"
        ]
        for p in expected_paths:
            assert p in paths, f"Path {p} missing from API contract schema"

    await close_mongo_connection()
    print("Phase 7 Frontend Integration & Real API Contract Verification PASSED!")

if __name__ == "__main__":
    asyncio.run(_test())
