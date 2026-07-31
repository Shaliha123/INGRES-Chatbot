import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryItem
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user
from backend.app.services.ai_service import generate_gemini_response
from backend.app.services.intent_service import orchestrate_intent_workflow

router = APIRouter(prefix="/api/v1/chat", tags=["Chat & RAG System"])

def format_history_item(doc: dict) -> ChatHistoryItem:
    return ChatHistoryItem(
        id=str(doc["_id"]),
        conversation_id=doc.get("conversation_id", ""),
        question=doc.get("question", ""),
        response=doc.get("response", ""),
        sources_used=doc.get("sources_used", []),
        intent=doc.get("intent", "GENERAL"),
        location_data=doc.get("location_data"),
        weather_data=doc.get("weather_data"),
        water_quality_data=doc.get("water_quality_data"),
        groundwater_records=doc.get("groundwater_records"),
        timestamp=str(doc.get("timestamp", ""))
    )

@router.post("", response_model=APIResponse[ChatMessageResponse])
async def send_chat_message(
    payload: ChatMessageRequest,
    current_user: dict = Depends(get_current_user)
):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question content cannot be empty")
        
    conversation_id = payload.conversation_id if payload.conversation_id else str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    # 1. Conversation Manager Processing
    from backend.app.services.conversation_manager import conversation_manager
    context, resolved_query, new_entities = await conversation_manager.process_message(
        payload.question, conversation_id, db.db.chat_history, []
    )
    
    # 2. Execute Production-Grade Agentic AI Pipeline
    from backend.app.services.retrieval_orchestrator import orchestrate_production_pipeline
    
    pipeline_res = await orchestrate_production_pipeline(resolved_query, context)
    
    ai_response = pipeline_res.get("response", "")
    sources_used = pipeline_res.get("sources_used", [])
    location_data = pipeline_res.get("location_data")
    weather_data = pipeline_res.get("weather_data")
    water_quality_data = pipeline_res.get("water_quality_data")
    groundwater_records = pipeline_res.get("groundwater_records")
    intent = pipeline_res.get("plan", {}).get("user_objective", "GENERAL")
    
    # Calculate updated conversation state
    updated_state = context.conversation_state.dict()
    updated_state["current_topic"] = intent if intent != "GENERAL" else updated_state.get("current_topic", "GENERAL")
    updated_state["last_tool"] = pipeline_res.get("plan", {}).get("sub_tasks", [""])[0] if pipeline_res.get("plan", {}).get("sub_tasks") else updated_state.get("last_tool")
    
    if pipeline_res.get("plan", {}).get("entities"):
        updated_state["entities"]["district"] = pipeline_res["plan"]["entities"][0]
        
    updated_state["active_sources"] = sources_used
    updated_state["timestamp"] = now

    # 3. Store conversation in MongoDB Atlas chat_history collection with enriched metadata
    chat_doc = {
        "user_id": current_user["id"],
        "user_email": current_user["email"],
        "conversation_id": conversation_id,
        "question": payload.question,
        "resolved_query": resolved_query,
        "response": ai_response,
        "sources_used": sources_used,
        "intent": intent,
        "location_data": location_data,
        "weather_data": weather_data,
        "water_quality_data": water_quality_data,
        "groundwater_records": groundwater_records,
        "state": updated_state,
        "timestamp": now
    }
    
    res = await db.db.chat_history.insert_one(chat_doc)
    chat_doc["_id"] = res.inserted_id
    
    # Update user activity in analytics collection asynchronously
    await db.db.analytics.update_one(
        {"type": "global_metrics"},
        {"$inc": {"total_chats": 1}, "$set": {"last_updated": now}},
        upsert=True
    )

    return APIResponse(
        success=True,
        message="Response generated successfully",
        data=ChatMessageResponse(
            id=str(res.inserted_id),
            conversation_id=conversation_id,
            question=payload.question,
            response=ai_response,
            sources_used=sources_used,
            intent=intent,
            location_data=location_data,
            weather_data=weather_data,
            water_quality_data=water_quality_data,
            groundwater_records=groundwater_records,
            timestamp=now
        )
    )

@router.get("/history", response_model=APIResponse[List[ChatHistoryItem]])
async def get_chat_history(
    conversation_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    if conversation_id:
        query["conversation_id"] = conversation_id
        
    cursor = db.db.chat_history.find(query).sort("timestamp", -1)
    history = []
    async for doc in cursor:
        history.append(format_history_item(doc))
        
    return APIResponse(
        success=True,
        message=f"Retrieved {len(history)} chat history records",
        data=history
    )

@router.delete("/history", response_model=APIResponse[dict])
async def clear_chat_history(
    conversation_id: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    query = {"user_id": current_user["id"]}
    if conversation_id:
        query["conversation_id"] = conversation_id
        
    res = await db.db.chat_history.delete_many(query)
    
    return APIResponse(
        success=True,
        message=f"Deleted {res.deleted_count} history records",
        data={"deleted_count": res.deleted_count}
    )
