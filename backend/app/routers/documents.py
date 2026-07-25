import os
import shutil
from typing import List
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from bson import ObjectId
from backend.app.database import db
from backend.app.schemas.document import DocumentResponse
from backend.app.schemas.common import APIResponse
from backend.app.middleware.auth import get_current_user
from backend.app.config import BASE_DIR

router = APIRouter(prefix="/api/v1/documents", tags=["Document Management"])

UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def extract_text_from_file(file_path: Path, file_ext: str) -> str:
    """Extract plain text content from PDF, DOCX, or TXT files."""
    text_content = ""
    try:
        if file_ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            for page in reader.pages:
                text_content += page.extract_text() or ""
        elif file_ext == ".docx":
            import docx
            doc = docx.Document(str(file_path))
            text_content = "\n".join([p.text for p in doc.paragraphs if p.text])
        elif file_ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text_content = f.read()
    except Exception as e:
        text_content = f"Text extraction warning: {str(e)}"
        
    return text_content.strip()

def format_document_doc(doc: dict) -> DocumentResponse:
    text_preview = doc.get("extracted_text", "")
    if text_preview and len(text_preview) > 200:
        text_preview = text_preview[:200] + "..."
        
    return DocumentResponse(
        id=str(doc["_id"]),
        title=doc.get("title", doc.get("filename", "")),
        filename=doc.get("filename", ""),
        file_type=doc.get("file_type", ""),
        file_size_bytes=doc.get("file_size_bytes", 0),
        uploaded_by=doc.get("uploaded_by", ""),
        upload_date=str(doc.get("upload_date", "")),
        extracted_text_preview=text_preview,
        storage_path=doc.get("storage_path", "")
    )

@router.post("", response_model=APIResponse[DocumentResponse])
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
        
    file_ext = Path(file.filename).suffix.lower()
    allowed_extensions = [".pdf", ".docx", ".txt", ".md", ".csv"]
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{file_ext}'. Allowed formats: {', '.join(allowed_extensions)}"
        )
        
    # Generate unique filename for storage
    timestamp_prefix = int(datetime.now(timezone.utc).timestamp())
    safe_filename = f"{timestamp_prefix}_{file.filename.replace(' ', '_')}"
    target_path = UPLOAD_DIR / safe_filename
    
    # Save file to disk
    try:
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    file_size = target_path.stat().st_size
    extracted_text = extract_text_from_file(target_path, file_ext)
    now = datetime.now(timezone.utc).isoformat()
    doc_title = title if title else file.filename
    
    document_doc = {
        "title": doc_title,
        "filename": file.filename,
        "storage_filename": safe_filename,
        "file_type": file_ext,
        "file_size_bytes": file_size,
        "uploaded_by": current_user["email"],
        "user_id": current_user["id"],
        "upload_date": now,
        "extracted_text": extracted_text,
        "storage_path": str(target_path)
    }
    
    res = await db.db.documents.insert_one(document_doc)
    document_doc["_id"] = res.inserted_id
    
    # Automatically add document content to Knowledge Base for RAG if text extraction succeeded
    if extracted_text and len(extracted_text) > 20:
        kb_entry = {
            "title": f"Doc: {doc_title}",
            "category": "Document Import",
            "content": extracted_text,
            "keywords": [file.filename, file_ext, "document_upload"],
            "source": f"Uploaded File: {file.filename}",
            "created_by": current_user["id"],
            "created_at": now,
            "updated_at": now
        }
        await db.db.knowledge_base.insert_one(kb_entry)
    
    return APIResponse(
        success=True,
        message="Document uploaded and processed successfully",
        data=format_document_doc(document_doc)
    )

@router.get("", response_model=APIResponse[List[DocumentResponse]])
async def list_documents():
    cursor = db.db.documents.find().sort("upload_date", -1)
    results = []
    async for doc in cursor:
        results.append(format_document_doc(doc))
        
    return APIResponse(
        success=True,
        message=f"Retrieved {len(results)} documents",
        data=results
    )

@router.get("/{doc_id}", response_model=APIResponse[DocumentResponse])
async def get_document(doc_id: str):
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
        
    doc = await db.db.documents.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    return APIResponse(
        success=True,
        message="Document retrieved successfully",
        data=format_document_doc(doc)
    )

@router.delete("/{doc_id}", response_model=APIResponse[dict])
async def delete_document(
    doc_id: str,
    current_user: dict = Depends(get_current_user)
):
    try:
        obj_id = ObjectId(doc_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid document ID format")
        
    doc = await db.db.documents.find_one({"_id": obj_id})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    # Check if storage file exists and delete it
    storage_path = Path(doc.get("storage_path", ""))
    if storage_path.exists():
        try:
            storage_path.unlink()
        except Exception:
            pass
            
    await db.db.documents.delete_one({"_id": obj_id})
    
    return APIResponse(
        success=True,
        message="Document deleted successfully",
        data={"doc_id": doc_id}
    )
