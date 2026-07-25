from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.knowledge import KnowledgeCreate, KnowledgeUpdate, KnowledgeResponse
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge Base"])

def format_kb_doc(doc: dict) -> KnowledgeResponse:
    return KnowledgeResponse(
        id=str(doc["_id"]),
        title=doc.get("title", ""),
        category=doc.get("category", "General"),
        content=doc.get("content", ""),
        keywords=doc.get("keywords", []),
        source=doc.get("source", "INGRES"),
        created_at=str(doc.get("created_at", "")),
        updated_at=str(doc.get("updated_at", ""))
    )

@router.get("", response_model=APIResponse[List[KnowledgeResponse]])
async def list_knowledge(
    q: Optional[str] = Query(None, description="Search query string"),
    category: Optional[str] = Query(None, description="Category filter")
):
    filter_query = {}
    if category:
        filter_query["category"] = category
    if q:
        filter_query["$or"] = [
            {"title": {"$regex": q, "$options": "i"}},
            {"content": {"$regex": q, "$options": "i"}},
            {"keywords": {"$regex": q, "$options": "i"}}
        ]
        
    cursor = db.db.knowledge_base.find(filter_query).sort("created_at", -1)
    results = []
    async for doc in cursor:
        results.append(format_kb_doc(doc))
        
    return APIResponse(
        success=True,
        message=f"Retrieved {len(results)} knowledge base items",
        data=results
    )

@router.get("/{item_id}", response_model=APIResponse[KnowledgeResponse])
async def get_knowledge_item(item_id: str):
    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
        
    doc = await db.db.knowledge_base.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
    return APIResponse(
        success=True,
        message="Knowledge base item retrieved successfully",
        data=format_kb_doc(doc)
    )

@router.post("", response_model=APIResponse[KnowledgeResponse])
async def create_knowledge_item(
    payload: KnowledgeCreate,
    current_user: dict = Depends(get_current_user)
):
    now = datetime.now(timezone.utc).isoformat()
    new_doc = {
        "title": payload.title,
        "category": payload.category,
        "content": payload.content,
        "keywords": payload.keywords,
        "source": payload.source,
        "created_by": current_user["id"],
        "created_at": now,
        "updated_at": now
    }
    
    res = await db.db.knowledge_base.insert_one(new_doc)
    new_doc["_id"] = res.inserted_id
    
    return APIResponse(
        success=True,
        message="Knowledge base item created successfully",
        data=format_kb_doc(new_doc)
    )

@router.put("/{item_id}", response_model=APIResponse[KnowledgeResponse])
async def update_knowledge_item(
    item_id: str,
    payload: KnowledgeUpdate,
    current_user: dict = Depends(get_current_user)
):
    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
        
    existing = await db.db.knowledge_base.find_one({"_id": obj_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
    updates = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if payload.title is not None:
        updates["title"] = payload.title
    if payload.category is not None:
        updates["category"] = payload.category
    if payload.content is not None:
        updates["content"] = payload.content
    if payload.keywords is not None:
        updates["keywords"] = payload.keywords
    if payload.source is not None:
        updates["source"] = payload.source
        
    await db.db.knowledge_base.update_one({"_id": obj_id}, {"$set": updates})
    updated = await db.db.knowledge_base.find_one({"_id": obj_id})
    
    return APIResponse(
        success=True,
        message="Knowledge base item updated successfully",
        data=format_kb_doc(updated)
    )

@router.delete("/{item_id}", response_model=APIResponse[dict])
async def delete_knowledge_item(
    item_id: str,
    admin_user: dict = Depends(require_admin)
):
    try:
        obj_id = ObjectId(item_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid item ID format")
        
    res = await db.db.knowledge_base.delete_one({"_id": obj_id})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
    return APIResponse(
        success=True,
        message="Knowledge base item deleted successfully",
        data={"item_id": item_id}
    )
