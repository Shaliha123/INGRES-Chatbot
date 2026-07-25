import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryItem
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user
from backend.app.services.ai_service import search_relevant_knowledge, generate_gemini_response

router = APIRouter(prefix="/api/v1/chat", tags=["Chat & RAG System"])

def format_history_item(doc: dict) -> ChatHistoryItem:
    return ChatHistoryItem(
        id=str(doc["_id"]),
        conversation_id=doc.get("conversation_id", ""),
        question=doc.get("question", ""),
        response=doc.get("response", ""),
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
    
    # 1. Search knowledge base and uploaded documents for relevant context
    context_text, sources_used = await search_relevant_knowledge(payload.question)
    
    # 2. Invoke Gemini AI model to generate contextual response
    ai_response = await generate_gemini_response(payload.question, context_text)
    
    # 3. Store conversation in MongoDB Atlas chat_history collection
    chat_doc = {
        "user_id": current_user["id"],
        "user_email": current_user["email"],
        "conversation_id": conversation_id,
        "question": payload.question,
        "response": ai_response,
        "sources_used": sources_used,
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
