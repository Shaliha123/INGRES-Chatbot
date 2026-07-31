import asyncio
import json
import logging
import httpx
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.app.config import settings

logger = logging.getLogger("ingres.tests")
logging.basicConfig(level=logging.INFO)

async def check_grounding(context: str, response: str) -> dict:
    """
    Automated Grounding Test.
    Uses LLM-as-a-judge to extract factual claims from the response and check if they are supported by the context.
    """
    system_prompt = """You are a strict Grounding Evaluator.
Given a CONTEXT and a RESPONSE, your job is to extract every factual claim made in the RESPONSE and verify if it is strictly supported by the CONTEXT.

Output ONLY a JSON object in this exact format:
{
  "claims": [
    {
      "claim": "The exact factual claim",
      "supported": true or false
    }
  ]
}
If there are no factual claims, output {"claims": []}.
Do not output markdown blocks or any other text, just raw JSON.
"""

    prompt = f"=== CONTEXT ===\n{context}\n\n=== RESPONSE ===\n{response}\n"

    # Try Groq first since OpenRouter free tier slugs change often
    api_key = settings.GROQ_API_KEY
    if api_key and len(api_key) > 10:
        url = "https://api.groq.com/openai/v1/chat/completions"
        model = "llama-3.3-70b-versatile"
    else:
        api_key = settings.OPENROUTER_API_KEY
        url = "https://openrouter.ai/api/v1/chat/completions"
        model = "meta-llama/llama-3.1-8b-instruct"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.0,
        "response_format": {"type": "json_object"}
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.post(url, headers=headers, json=payload)
            if res.status_code == 200:
                data = res.json()
                content = data["choices"][0]["message"]["content"].strip()
                
                # Cleanup potential markdown ticks if model ignored instructions
                if content.startswith("```json"):
                    content = content[7:-3].strip()
                elif content.startswith("```"):
                    content = content[3:-3].strip()
                    
                return json.loads(content)
            else:
                logger.error(f"Judge LLM Failed: {res.text}")
                return {"claims": []}
        except Exception as e:
            logger.error(f"Error during grounding evaluation: {e}")
            return {"claims": []}

async def test_regression_grounding():
    print("Running Grounding Regression Test...")
    
    test_cases = [
        {
            "name": "Well-Grounded Response",
            "context": "The pre-monsoon water depth in Salem is 8.2 meters below ground level.",
            "response": "According to the provided data, the pre-monsoon depth in Salem is 8.2 m."
        },
        {
            "name": "Hallucinated Response",
            "context": "The pre-monsoon water depth in Salem is 8.2 meters below ground level.",
            "response": "Salem pre-monsoon depth is 8.2 m. However, groundwater is declining nationwide according to USGS reports."
        }
    ]

    all_passed = True

    for i, case in enumerate(test_cases):
        print(f"\nEvaluating Case {i+1}: {case['name']}")
        result = await check_grounding(case["context"], case["response"])
        
        has_unsupported = False
        print("Findings:")
        for claim in result.get("claims", []):
            status = "[PASS]" if claim.get("supported") else "[FAIL]"
            print(f"  {status} | {claim.get('claim')}")
            if not claim.get("supported"):
                has_unsupported = True
                
        if has_unsupported:
            print("[FAIL] TEST FAILED: Unsupported claims detected in the response.")
            if case["name"] != "Hallucinated Response":
                all_passed = False
        else:
            print("[PASS] TEST PASSED: All claims strictly supported by evidence.")
            if case["name"] == "Hallucinated Response":
                # If a hallucinated response passes, the test itself is failing to detect it
                all_passed = False

    if all_passed:
        print("\nAll Grounding Regression Tests Passed Successfully!")
        sys.exit(0)
    else:
        print("\nGrounding Regression Tests Failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(test_regression_grounding())
