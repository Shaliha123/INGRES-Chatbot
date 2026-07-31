import asyncio
import httpx
from pydantic import BaseModel

async def main():
    # 1. Login
    async with httpx.AsyncClient() as client:
        res = await client.post("http://127.0.0.1:8000/api/v1/login", json={"email": "test@example.com", "password": "password"})
        if res.status_code != 200:
            print("Login failed:", res.text)
            return
            
        token = res.json()["data"]["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Chat
        queries = [
            "summarise district wise ground water level",
            "Show groundwater status in Salem",
            "What is the exact details of ground water level in Tamil Nadu state wise?"
        ]
        
        for q in queries:
            print(f"\n--- Question: {q} ---")
            chat_res = await client.post("http://127.0.0.1:8000/api/v1/chat", json={"question": q, "conversation_id": "test-session"}, headers=headers, timeout=30.0)
            if chat_res.status_code == 200:
                print(chat_res.json()["data"]["response"])
            else:
                print(f"Error {chat_res.status_code}: {chat_res.text}")

if __name__ == "__main__":
    asyncio.run(main())
