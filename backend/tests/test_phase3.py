import asyncio
import httpx
from backend.app.database import connect_to_mongo, close_mongo_connection, db
from backend.app.utils.security import hash_password, verify_password, create_access_token, decode_access_token
from backend.app.main import app

async def _test():
    await connect_to_mongo()
    
    # Test Password Hashing
    pass_plain = "INGRESSecretPass2026!"
    pass_hash = hash_password(pass_plain)
    assert verify_password(pass_plain, pass_hash) is True
    assert verify_password("WrongPassword", pass_hash) is False
    
    # Test JWT Token
    token = create_access_token({"sub": "test_user_123", "role": "Admin"})
    decoded = decode_access_token(token)
    assert decoded["sub"] == "test_user_123"
    assert decoded["role"] == "Admin"
    
    # Clean up previous test users if any
    await db.db.users.delete_many({"email": {"$in": ["testuser_p3@ingres.gov.in", "admin_p3@ingres.gov.in"]}})
    
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Register Regular User
        res_reg = await client.post("/api/v1/register", json={
            "name": "Test User Phase 3",
            "email": "testuser_p3@ingres.gov.in",
            "password": "Password123!",
            "role": "User"
        })
        assert res_reg.status_code == 200, res_reg.text
        user_data = res_reg.json()
        assert user_data["success"] is True
        user_token = user_data["data"]["access_token"]
        
        # 2. Register Admin User
        res_admin_reg = await client.post("/api/v1/register", json={
            "name": "Admin Phase 3",
            "email": "admin_p3@ingres.gov.in",
            "password": "AdminPassword123!",
            "role": "Admin"
        })
        assert res_admin_reg.status_code == 200, res_admin_reg.text
        admin_token = res_admin_reg.json()["data"]["access_token"]
        
        # 3. Test Profile Retrieval
        res_prof = await client.get("/api/v1/profile", headers={"Authorization": f"Bearer {user_token}"})
        assert res_prof.status_code == 200
        assert res_prof.json()["data"]["email"] == "testuser_p3@ingres.gov.in"
        
        # 4. Test User List via Admin Token
        res_users = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {admin_token}"})
        assert res_users.status_code == 200
        users_list = res_users.json()["data"]
        assert len(users_list) >= 2

    # Clean up created test users
    await db.db.users.delete_many({"email": {"$in": ["testuser_p3@ingres.gov.in", "admin_p3@ingres.gov.in"]}})

    await close_mongo_connection()
    print("Phase 3 Authentication & User Management Verification PASSED!")

if __name__ == "__main__":
    asyncio.run(_test())
