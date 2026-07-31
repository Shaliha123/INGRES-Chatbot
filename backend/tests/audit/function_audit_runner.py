import asyncio
import json
import os
import sys
import time
import inspect
from functools import wraps
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from backend.app.database import connect_to_mongo, close_mongo_connection

import backend.app.services.retrieval_orchestrator as orchestrator
import backend.app.services.ai_planner as ai_planner
import backend.app.services.dynamic_retriever as dynamic_retriever
from backend.app.services.tool_registry import tool_registry, MapTool, WeatherTool, DocumentTool, WaterQualityTool
import backend.app.services.ai_service as ai_service
import backend.app.services.evidence_scorer as evidence_scorer
import backend.app.services.context_compressor as context_compressor
import backend.app.services.evidence_validator as evidence_validator
import backend.app.services.reflection_engine as reflection_engine
import motor.motor_asyncio

trace_log = {}
current_q = ""

def safe_serialize(obj):
    try:
        if hasattr(obj, "dict"):
            return obj.dict()
        if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
            return obj
        return str(obj)[:200]
    except Exception:
        return "<Unserializable>"

def get_caller_info():
    stack = inspect.stack()
    # Find first caller not in this script
    for frame in stack[2:]:
        if "function_audit_runner.py" not in frame.filename:
            return f"{os.path.basename(frame.filename)}:{frame.lineno}"
    return "Unknown"

def trace_func(func_name, is_db=False):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.perf_counter()
                caller = get_caller_info()
                try:
                    res = await func(*args, **kwargs)
                    duration = (time.perf_counter() - start) * 1000
                    log_entry = {
                        "function": func_name,
                        "executed": "YES",
                        "caller": caller,
                        "duration_ms": round(duration, 2),
                        "args": [safe_serialize(a) for a in args],
                        "kwargs": {k: safe_serialize(v) for k, v in kwargs.items()},
                        "returned": safe_serialize(res)
                    }
                    if "execution_trace" not in trace_log[current_q]:
                        trace_log[current_q]["execution_trace"] = []
                    trace_log[current_q]["execution_trace"].append(log_entry)
                    return res
                except Exception as e:
                    duration = (time.perf_counter() - start) * 1000
                    log_entry = {
                        "function": func_name,
                        "executed": "YES (Failed)",
                        "caller": caller,
                        "duration_ms": round(duration, 2),
                        "args": [safe_serialize(a) for a in args],
                        "kwargs": {k: safe_serialize(v) for k, v in kwargs.items()},
                        "error": str(e)
                    }
                    if "execution_trace" not in trace_log[current_q]:
                        trace_log[current_q]["execution_trace"] = []
                    trace_log[current_q]["execution_trace"].append(log_entry)
                    raise e
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.perf_counter()
                caller = get_caller_info()
                try:
                    res = func(*args, **kwargs)
                    duration = (time.perf_counter() - start) * 1000
                    log_entry = {
                        "function": func_name,
                        "executed": "YES",
                        "caller": caller,
                        "duration_ms": round(duration, 2),
                        "args": [safe_serialize(a) for a in args],
                        "kwargs": {k: safe_serialize(v) for k, v in kwargs.items()},
                        "returned": safe_serialize(res)
                    }
                    if "execution_trace" not in trace_log[current_q]:
                        trace_log[current_q]["execution_trace"] = []
                    trace_log[current_q]["execution_trace"].append(log_entry)
                    return res
                except Exception as e:
                    duration = (time.perf_counter() - start) * 1000
                    log_entry = {
                        "function": func_name,
                        "executed": "YES (Failed)",
                        "caller": caller,
                        "duration_ms": round(duration, 2),
                        "args": [safe_serialize(a) for a in args],
                        "kwargs": {k: safe_serialize(v) for k, v in kwargs.items()},
                        "error": str(e)
                    }
                    if "execution_trace" not in trace_log[current_q]:
                        trace_log[current_q]["execution_trace"] = []
                    trace_log[current_q]["execution_trace"].append(log_entry)
                    raise e
            return sync_wrapper
    return decorator

def patch_db_find(func):
    @wraps(func)
    def wrapper(self, filter=None, *args, **kwargs):
        start = time.perf_counter()
        caller = get_caller_info()
        res = func(self, filter, *args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        
        # We can't await the cursor fully without consuming it, so we just log the query
        log_entry = {
            "function": f"MongoDB Query ({self.name})",
            "executed": "YES",
            "caller": caller,
            "duration_ms": round(duration, 2),
            "args": [{"collection": self.name, "filter": safe_serialize(filter)}],
            "kwargs": {},
            "returned": "<AsyncCursor>"
        }
        if "execution_trace" not in trace_log[current_q]:
            trace_log[current_q]["execution_trace"] = []
        trace_log[current_q]["execution_trace"].append(log_entry)
        return res
    return wrapper

# Apply wrappers
orchestrator.orchestrate_production_pipeline = trace_func("orchestrate_production_pipeline")(orchestrator.orchestrate_production_pipeline)
ai_planner.analyze_user_objective = trace_func("analyze_user_objective")(ai_planner.analyze_user_objective)

if hasattr(dynamic_retriever, "execute_dynamic_retrieval"):
    dynamic_retriever.execute_dynamic_retrieval = trace_func("execute_dynamic_retrieval")(dynamic_retriever.execute_dynamic_retrieval)

ai_service.search_relevant_knowledge = trace_func("search_relevant_knowledge")(ai_service.search_relevant_knowledge)
ai_service.generate_gemini_response = trace_func("generate_gemini_response")(ai_service.generate_gemini_response)
ai_service.synthesize_rag_response = trace_func("synthesize_rag_response")(ai_service.synthesize_rag_response)

evidence_scorer.score_retrieved_evidence = trace_func("score_retrieved_evidence")(evidence_scorer.score_retrieved_evidence)
context_compressor.compress_context = trace_func("compress_context")(context_compressor.compress_context)
evidence_validator.validate_retrieved_evidence = trace_func("validate_retrieved_evidence")(evidence_validator.validate_retrieved_evidence)
reflection_engine.reflect_on_answer = trace_func("reflect_on_answer")(reflection_engine.reflect_on_answer)

motor.motor_asyncio.AsyncIOMotorCollection.find = patch_db_find(motor.motor_asyncio.AsyncIOMotorCollection.find)

# Wrap tools
for tool_name, tool_inst in tool_registry._tools.items():
    tool_inst.execute = trace_func(f"ToolRegistry.{tool_inst.__class__.__name__}.execute")(tool_inst.execute)

async def run_audit():
    await connect_to_mongo()
    
    questions = [
        "What is the groundwater status in Salem?",
        "Which districts are declining in Tamil Nadu?",
        "Show groundwater levels",
        "Is the water in Chennai safe for drinking?",
        "Will rainfall improve groundwater recharge in Coimbatore this week?"
    ]
    
    for q in questions:
        global current_q
        current_q = q
        trace_log[q] = {"execution_trace": []}
        print(f"Running query: {q}")
        try:
            res = await orchestrator.orchestrate_production_pipeline(q)
            trace_log[q]["final_pipeline_result"] = safe_serialize(res)
        except Exception as e:
            trace_log[q]["error"] = str(e)
            
    with open("function_audit_traces.json", "w", encoding="utf-8") as f:
        json.dump(trace_log, f, indent=2, ensure_ascii=False)
        
    await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(run_audit())
