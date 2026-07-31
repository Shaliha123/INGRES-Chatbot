import asyncio
import json
from datetime import datetime
from backend.app.main import app
from backend.app.middleware.auth import get_current_user
from backend.app.utils.security import create_access_token
from httpx import AsyncClient

# Suppress noisy logs
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

token = create_access_token({"sub": "test@test.com", "id": "test_id"})
headers = {"Authorization": f"Bearer {token}"}

async def mock_get_current_user():
    return {"id": "test_id", "email": "test@test.com"}

app.dependency_overrides[get_current_user] = mock_get_current_user

async def run_audit():
    query = "What is the groundwater status in Salem?"
    
    from backend.app.database import db, connect_to_mongo
    await connect_to_mongo()
    
    from unittest.mock import patch
    import httpx
    
    original_post = httpx.AsyncClient.post
    
    audit_data = {}
    
    async def patched_post(self, url, *args, **kwargs):
        if "googleapis.com" in url or "api.openai.com" in url or "api.groq.com" in url or "openrouter.ai" in url:
            payload = kwargs.get('json', {})
            if "googleapis.com" in url:
                prompt = payload.get("contents", [{}])[0].get("parts", [{}])[0].get("text", "")
            else:
                messages = payload.get("messages", [])
                prompt = json.dumps(messages, indent=2)
                
            if "prompt" not in audit_data:
                audit_data["prompt"] = prompt
                
            resp = await original_post(self, url, *args, **kwargs)
            if resp.status_code == 200 and "raw_response" not in audit_data:
                audit_data["raw_response"] = resp.text
            return resp
        else:
            return await original_post(self, url, *args, **kwargs)
            
    async with AsyncClient(app=app, base_url="http://test") as client:
        with patch("httpx.AsyncClient.post", new=patched_post):
            res = await client.post("/api/v1/chat", json={"question": query, "conversation_id": "audit"}, headers=headers)
            if res.status_code == 200:
                audit_data["frontend_output"] = res.json().get("data", {}).get("response")
                
    with open("audit_results_new.json", "w") as f:
        json.dump(audit_data, f, indent=2)
        
    print("Audit finished.")

if __name__ == "__main__":
    asyncio.run(run_audit())
