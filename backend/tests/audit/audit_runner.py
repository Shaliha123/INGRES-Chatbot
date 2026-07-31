import asyncio
import json
import os
import sys
from unittest.mock import patch
import httpx
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "backend", ".env"))

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.app.database import connect_to_mongo, close_mongo_connection
from backend.app.services.retrieval_orchestrator import orchestrate_production_pipeline
from backend.app.services.ai_planner import analyze_user_objective
from backend.app.services.tool_registry import BaseTool
import backend.app.services.ai_service as ai_service
import backend.app.services.evidence_scorer as evidence_scorer
import backend.app.services.context_compressor as context_compressor
import backend.app.services.evidence_validator as evidence_validator
import backend.app.services.reflection_engine as reflection_engine

# Patches and interceptions
trace_log = {}
current_q = ""

original_analyze_user_objective = analyze_user_objective
# original_execute removed
original_search_relevant_knowledge = ai_service.search_relevant_knowledge
original_score_retrieved_evidence = evidence_scorer.score_retrieved_evidence
original_compress_context = context_compressor.compress_context
original_validate_retrieved_evidence = evidence_validator.validate_retrieved_evidence
original_reflect_on_answer = reflection_engine.reflect_on_answer
original_post = httpx.AsyncClient.post

def patch_analyze_user_objective(query, history=None):
    plan = original_analyze_user_objective(query, history)
    trace_log[current_q]["planner"] = {
        "intent": plan.user_objective,
        "entities": plan.entities,
        "objectives": plan.sub_tasks,
        "capabilities": plan.needs.dict(),
        "is_ambiguous": plan.is_ambiguous,
        "clarification_prompt": plan.clarification_prompt
    }
    return plan

# patch_tool_execute removed from global scope

async def patch_search_relevant_knowledge(query, limit=4):
    context, sources = await original_search_relevant_knowledge(query, limit)
    trace_log[current_q]["vector_search"] = {
        "query": query,
        "context": context,
        "sources": sources
    }
    return context, sources

def patch_score_retrieved_evidence(query, evidence_text, source_title):
    score = original_score_retrieved_evidence(query, evidence_text, source_title)
    if "evidence_scoring" not in trace_log[current_q]:
        trace_log[current_q]["evidence_scoring"] = []
    trace_log[current_q]["evidence_scoring"].append({
        "source": source_title,
        "text": evidence_text,
        "score": score.dict()
    })
    return score

def patch_compress_context(raw_context_blocks, query, max_tokens=750):
    compressed = original_compress_context(raw_context_blocks, query, max_tokens)
    trace_log[current_q]["context_compression"] = {
        "raw_blocks": raw_context_blocks,
        "compressed": compressed
    }
    return compressed

def patch_validate_retrieved_evidence(query, retrieved_context, plan_dict):
    val = original_validate_retrieved_evidence(query, retrieved_context, plan_dict)
    trace_log[current_q]["evidence_validation"] = val.dict()
    return val

original_generate_gemini_response = ai_service.generate_gemini_response

async def patch_generate_gemini_response(question, context):
    trace_log[current_q]["gemini_prompt_context"] = context
    trace_log[current_q]["gemini_question"] = question
    
    mock_response = f"Based on the following evidence:\n{context}\n\nI am answering: {question}"
    trace_log[current_q]["gemini_raw_response"] = {"mocked": mock_response}
    return mock_response

def patch_reflect_on_answer(query, generated_answer, context):
    passed, feedback = original_reflect_on_answer(query, generated_answer, context)
    trace_log[current_q]["reflection"] = {
        "generated_answer": generated_answer,
        "passed": passed,
        "feedback": feedback
    }
    return passed, feedback

import motor.motor_asyncio
original_find = motor.motor_asyncio.AsyncIOMotorCollection.find
def patch_find(self, filter=None, *args, **kwargs):
    if "mongo_queries" not in trace_log[current_q]:
        trace_log[current_q]["mongo_queries"] = []
    trace_log[current_q]["mongo_queries"].append({
        "collection": self.name,
        "filter": filter
    })
    return original_find(self, filter, *args, **kwargs)

async def run_audit():
    await connect_to_mongo()
    
    questions = [
        "What is the groundwater status in Salem?",
        "Which districts are declining in Tamil Nadu?",
        "Show groundwater levels",
        "Is the water in Chennai safe for drinking?",
        "Will rainfall improve groundwater recharge in Coimbatore this week?",
        "Compare the water depth between Vellore and Madurai.",
        "What is the coordinates for Tanjore?",
        "What are the findings from the uploaded report?",
        "Does crystalline charnockite affect water tables?",
        "What is the pH level in Rajasthan?",
        "Show me water quality for an unknown district XYZ."
    ]
    
    import backend.app.services.ai_planner
    backend.app.services.ai_planner.analyze_user_objective = patch_analyze_user_objective
    ai_service.search_relevant_knowledge = patch_search_relevant_knowledge
    evidence_scorer.score_retrieved_evidence = patch_score_retrieved_evidence
    context_compressor.compress_context = patch_compress_context
    evidence_validator.validate_retrieved_evidence = patch_validate_retrieved_evidence
    reflection_engine.reflect_on_answer = patch_reflect_on_answer
    ai_service.generate_gemini_response = patch_generate_gemini_response
    motor.motor_asyncio.AsyncIOMotorCollection.find = patch_find
    
    from backend.app.services.tool_registry import tool_registry
    
    def get_patched_execute(original_method, tool_name):
        async def patched_execute(self, **kwargs):
            res = await original_method(**kwargs)
            if "tools" not in trace_log[current_q]:
                trace_log[current_q]["tools"] = []
            trace_log[current_q]["tools"].append({
                "tool_name": tool_name,
                "kwargs": kwargs,
                "result": str(res)[:500] + "..." if len(str(res)) > 500 else res
            })
            return res
        return patched_execute

    for tool in tool_registry._tools.values():
        tool.execute = get_patched_execute(tool.execute, tool.name).__get__(tool, type(tool))

    for q in questions:
        global current_q
        current_q = q
        trace_log[q] = {}
        print(f"Running query: {q}")
        try:
            res = await orchestrate_production_pipeline(q)
            trace_log[q]["final_pipeline_result"] = res
        except Exception as e:
            trace_log[q]["error"] = str(e)
            
    with open("audit_traces.json", "w", encoding="utf-8") as f:
        json.dump(trace_log, f, indent=2, ensure_ascii=False)
        
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_audit())
