import asyncio
import json
import logging
import httpx
from datetime import datetime
from unittest.mock import patch

from backend.app.main import app
from backend.app.config import settings
from backend.app.utils.security import create_access_token
from httpx import AsyncClient

# Suppress noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)

test_questions = [
    "What is the groundwater status in Salem?",
    "List all states that have groundwater data.",
    "Show groundwater reports.",
    "Will rainfall improve recharge in Coimbatore?",
    "Water quality in Chennai.",
    "Random unknown district."
]

token = create_access_token({"sub": "test@test.com", "id": "test_id"})
headers = {"Authorization": f"Bearer {token}"}

async def mock_get_current_user():
    return {"id": "test_id", "email": "test@test.com"}

from backend.app.middleware.auth import get_current_user
app.dependency_overrides[get_current_user] = mock_get_current_user

async def run_audit():
    print("Starting Chat Pipeline Runtime Verification Audit\n")
    print("=================================================\n")
    
    from backend.app.database import db, connect_to_mongo
    await connect_to_mongo()
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        
        # We will patch httpx.AsyncClient.post inside ai_service to capture LLM API calls
        original_post = httpx.AsyncClient.post
        
        for q in test_questions:
            print(f"--- Question: {q} ---")
            
            # State variables
            trace_state = {
                "planner": None,
                "mongo": [],
                "prompt": None,
                "llm_api": [],
                "frontend_response": None
            }
            
            async def patched_post(self, url, *args, **kwargs):
                nonlocal trace_state
                # Only capture LLM calls
                if "googleapis.com" in url or "api.openai.com" in url or "api.groq.com" in url or "openrouter.ai" in url:
                    payload = kwargs.get('json', {})
                    if "googleapis.com" in url:
                        prompt = payload.get("contents", [{}])[0].get("parts", [{}])[0].get("text", "")
                    else:
                        messages = payload.get("messages", [])
                        prompt = json.dumps(messages, indent=2)
                        
                    if not trace_state["prompt"]:
                        trace_state["prompt"] = prompt
                        print("\n[PROMPT CONSTRUCTED]:")
                        print("-" * 50)
                        print(prompt[:500] + "\n... [TRUNCATED] ..." if len(prompt) > 500 else prompt)
                        print("-" * 50 + "\n")
                        
                    provider = "Gemini" if "googleapis" in url else "OpenAI" if "openai" in url else "Groq" if "groq" in url else "OpenRouter"
                    
                    print(f"[LLM API -> {provider}] Endpoint: {url}")
                    start_t = datetime.now()
                    try:
                        resp = await original_post(self, url, *args, **kwargs)
                        latency = (datetime.now() - start_t).total_seconds()
                        print(f"[LLM API <- {provider}] Status: {resp.status_code}, Latency: {latency:.2f}s")
                        print(f"[LLM API RAW RESPONSE] {resp.text}\n")
                        
                        trace_state["llm_api"].append({
                            "provider": provider,
                            "status": resp.status_code,
                            "response_snippet": resp.text[:200] + "..." if len(resp.text) > 200 else resp.text,
                            "error": resp.status_code != 200
                        })
                        return resp
                    except Exception as e:
                        print(f"[LLM API ERROR <- {provider}] {e}")
                        trace_state["llm_api"].append({
                            "provider": provider,
                            "status": 0,
                            "error": str(e)
                        })
                        raise e
                else:
                    return await original_post(self, url, *args, **kwargs)
            
            with patch("httpx.AsyncClient.post", new=patched_post):
                print("[Frontend] Request sent to /api/v1/chat")
                res = await client.post("/api/v1/chat", json={"question": q, "conversation_id": "test_conv"}, headers=headers)
                
                print(f"[FastAPI] Response Status: {res.status_code}")
                if res.status_code == 200:
                    data = res.json()
                    print("[Frontend] Response parsed successfully")
                    trace_state["frontend_response"] = data.get("data", {}).get("response")
                    if trace_state['frontend_response']:
                        print(f"Final Output: {trace_state['frontend_response'][:200]}...\n")
                else:
                    print(f"[FastAPI Error] {res.text}\n")
            print("\n")

if __name__ == "__main__":
    asyncio.run(run_audit())
