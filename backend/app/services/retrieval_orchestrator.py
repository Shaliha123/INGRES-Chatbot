import logging
import asyncio
import time
from typing import Dict, Any, List, Optional
from backend.app.services.ai_planner import analyze_user_objective, AIPlan
from backend.app.services.tool_registry import tool_registry
from backend.app.services.evidence_scorer import score_retrieved_evidence
from backend.app.services.context_compressor import compress_context
from backend.app.services.evidence_validator import validate_retrieved_evidence
from backend.app.services.reflection_engine import reflect_on_answer
from backend.app.schemas.conversation import ConversationContext, ToolResult

logger = logging.getLogger("ingres.orchestrator")

async def orchestrate_production_pipeline(query: str, context: ConversationContext) -> Dict[str, Any]:
    """
    Next-Gen Production-Grade Orchestrator Architecture:
    User Question
      │
      ▼
    Question Understanding -> AI Planner
      │
      ▼
    Query Decomposition -> Capability Needs
      │
      ▼
    Tool Registry Dispatch -> Parallel Retrieval
      │
      ▼
    Evidence Scoring -> Context Compression -> Evidence Validation
      │
      ▼
    Gemini Reasoning Engine -> Reflection Engine -> Final Answer
    """
    start_time = time.time()
    # 1. AI Reasoning Planner
    logger.info(f"[Audit] Phase: Planner starting for query: '{query}'")
    # We pass the ConversationContext to the planner for advanced extraction
    plan: AIPlan = analyze_user_objective(query, context)
    logger.info(f"[Audit] Phase: Planner Output -> Intents: {plan.needs}, Tools queued: {[q.intent for q in plan.structured_queries] if plan.structured_queries else 'None'}")

    # 2. Dynamic Tool Dispatch
    tasks = []
    tool_names = []

    if plan.needs.need_spatial_map and plan.entities:
        map_tool = tool_registry.get_tool("map_tool")
        if map_tool:
            tasks.append(map_tool.execute(entity_name=plan.entities[0]))
            tool_names.append("map_tool")

    if plan.needs.need_rainfall_forecast:
        weather_tool = tool_registry.get_tool("weather_tool")
        if weather_tool:
            tasks.append(weather_tool.execute())
            tool_names.append("weather_tool")

    if plan.needs.need_water_quality:
        wq_tool = tool_registry.get_tool("water_quality_tool")
        if wq_tool:
            tasks.append(wq_tool.execute(entity_name=plan.entities[0] if plan.entities else "Regional"))
            tool_names.append("water_quality_tool")

    doc_tool = tool_registry.get_tool("document_tool")
    if doc_tool and not plan.needs.need_structured_data:
        if plan.needs.need_report_summary or plan.needs.need_groundwater_trends or plan.needs.need_district_statistics or not tasks:
            # Trigger document tool if reports/trends are needed, or as a default fallback if no other tool matched
            tasks.append(doc_tool.execute(query=query))
            tool_names.append("document_tool")
        
    structured_tool = tool_registry.get_tool("structured_data_tool")
    if structured_tool and plan.needs.need_structured_data:
        tasks.append(structured_tool.execute(structured_queries=plan.structured_queries))
        tool_names.append("structured_data_tool")

    # Run Parallel Tools
    logger.info(f"[Audit] Phase: Tool Selection complete. Selected tools: {tool_names}")
    logger.info(f"[Audit] Phase: Retrieval commencing via {len(tasks)} tools.")
    results = await asyncio.gather(*tasks, return_exceptions=True)
    logger.info(f"[Audit] Phase: Retrieval complete. Gathering results.")

    location_data = None
    weather_data = None
    water_quality_data = None
    context_blocks = []
    sources_used = []

    sources_used = []
    diagnostics_data = []

    for name, res in zip(tool_names, results):
        if isinstance(res, Exception):
            logger.error(f"Tool {name} execution error: {res}")
            continue
        
        # ToolResult extraction
        if not hasattr(res, "success"): continue
        
        if name == "map_tool" and res.success:
            location_data = res.payload
        if name == "weather_tool" and res.success:
            weather_data = res.payload
        if name == "water_quality_tool" and res.success:
            water_quality_data = res.payload
            
        if res.success and res.evidence:
            for ev in res.evidence:
                if isinstance(ev, dict) and "document_context" in ev:
                    context_blocks.append(ev["document_context"])
                elif isinstance(ev, str):
                    context_blocks.append(ev)
            if res.metadata.get("sources"):
                sources_used.extend(res.metadata["sources"])
            if res.metadata.get("diagnostics"):
                diagnostics_data.extend(res.metadata["diagnostics"])

    # 3. Multi-Dimensional Evidence Scoring
    scored_items = []
    for idx, block in enumerate(context_blocks):
        src_name = sources_used[idx] if idx < len(sources_used) else "Knowledge Base"
        score = score_retrieved_evidence(query, block, src_name)
        scored_items.append(score.dict())

    # 4. Context Compression
    compressed_context = compress_context(context_blocks, query)

    # 5. Pre-Synthesis Evidence Validation
    validation = validate_retrieved_evidence(query, compressed_context, plan.dict())
    logger.info(f"[Audit] Phase: Grounding Validator executed. Support status: {validation.evidence_supported}")

    # Build holistic context for reflection
    holistic_context = compressed_context
    if location_data: holistic_context += f"\nLocation Data: {location_data}"
    if weather_data: holistic_context += f"\nWeather Data: {weather_data}"
    if water_quality_data: holistic_context += f"\nWater Quality Data: {water_quality_data}"

    # Retrieval Diagnostics Log
    logger.info("\n" + "="*50)
    logger.info("RETRIEVAL DIAGNOSTICS LOG")
    logger.info(f"User Query: '{query}'")
    if diagnostics_data:
        logger.info(f"Retrieved Chunks: {len(diagnostics_data)}")
        for i, diag in enumerate(diagnostics_data, 1):
            logger.info(f"\n{i}.")
            logger.info(f"Document: {diag.get('document')}")
            logger.info(f"Page: {diag.get('page')}")
            logger.info(f"Chunk: {diag.get('chunk_index')}")
            logger.info(f"Section: {diag.get('section')}")
            logger.info(f"Vector Similarity: {diag.get('vec_score', 0):.2f}")
            logger.info(f"Keyword Score: {diag.get('keyword_score', 0):.2f}")
            logger.info(f"Final Rank: {diag.get('rank')}")
            logger.info(f"Neighbor Expansion: {diag.get('neighbor_expansion')}")
            logger.info(f"Included: YES")
    else:
        logger.info(f"Retrieved Chunks: {len(context_blocks)}")
        if scored_items:
            for item in scored_items:
                logger.info(f"- Source: {item.get('source_name', 'Unknown')}")
                logger.info(f"  Similarity/Score: {item.get('composite_confidence', 0.0)}")
                
    logger.info(f"\nEvidence Found: {'YES' if validation.evidence_supported else 'NO'}")
    logger.info("="*50 + "\n")

    # 6. Gemini Synthesis & Reflection Self-Check
    logger.info(f"[Audit] Phase: Formatter (LLM Synthesis) commencing.")
    
    if not validation.evidence_supported:
        ai_response = "I couldn't find evidence in the retrieved documents to answer this question."
    else:
        from backend.app.services.ai_service import generate_gemini_response
        ai_response = await generate_gemini_response(query, holistic_context)

        is_passed, feedback = reflect_on_answer(query, ai_response, holistic_context)
        if not is_passed:
            logger.info(f"Reflection triggered re-synthesis: {feedback}")
            ai_response = await generate_gemini_response(query, f"{holistic_context}\nCRITICAL REASONING INSTRUCTION: {feedback}")
            
            # Second Reflection Check
            is_passed2, feedback2 = reflect_on_answer(query, ai_response, holistic_context)
            if not is_passed2:
                logger.warning(f"Second Reflection Failed: {feedback2}. Triggering Fallback.")
                ai_response = "I couldn't find evidence in the retrieved documents to answer this question."
                
    logger.info(f"Final Answer: {ai_response[:150]}...")

    elapsed = time.time() - start_time
    from backend.app.services.pipeline_evaluator import evaluate_pipeline_execution
    res_dict = {
        "merged_context": compressed_context,
        "evidence_scores": scored_items
    }
    eval_record = evaluate_pipeline_execution(query, plan.dict(), res_dict, ai_response, elapsed)

    return {
        "status": "success",
        "response": ai_response,
        "location_data": location_data,
        "weather_data": weather_data,
        "water_quality_data": water_quality_data,
        "merged_context": compressed_context,
        "sources_used": list(dict.fromkeys(sources_used)),
        "evidence_scores": scored_items,
        "plan": plan.dict(),
        "evaluation_record": eval_record.dict(),
        "diagnostics": diagnostics_data
    }
