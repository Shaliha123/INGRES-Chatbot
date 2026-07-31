import os
import re
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

def extract_text_from_file(file_path: Path, file_ext: str) -> List[dict]:
    """Extract plain text content from PDF, DOCX, or TXT files page by page."""
    pages = []
    try:
        if file_ext == ".pdf":
            from pypdf import PdfReader
            reader = PdfReader(str(file_path))
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({"page_number": i + 1, "text": text.strip()})
        elif file_ext == ".docx":
            import docx
            doc = docx.Document(str(file_path))
            text = "\n".join([p.text for p in doc.paragraphs if p.text])
            pages.append({"page_number": 1, "text": text.strip()})
        elif file_ext in [".txt", ".md", ".csv"]:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                pages.append({"page_number": 1, "text": f.read().strip()})
    except Exception as e:
        pages.append({"page_number": 1, "text": f"Text extraction warning: {str(e)}"})
        
    return pages

def extract_section_heading(text: str) -> str:
    """Detect section headings using multiple heuristics."""
    lines = text.splitlines()
    for line in lines[:5]: 
        line = line.strip()
        if not line: continue
        # Numbered heading e.g., 5.1 Seasonal Fluctuation
        if re.match(r'^\d+(\.\d+)+\s+[A-Z]', line):
            return line[:100]
        # All caps heading
        if line.isupper() and len(line) > 5 and len(line) < 60:
            return line
        # Title case heading
        if line.istitle() and len(line) > 5 and len(line) < 60:
            return line
    return "Unknown Section"

async def process_document_chunks(pages: List[dict], doc_id: str, doc_title: str):
    """Chunk pages, generate embeddings, and store in document_chunks."""
    from backend.app.services.ai_service import generate_embedding
    chunks = []
    chunk_index = 0
    chunk_size = 800
    overlap = 200
    current_section = "Introduction"
    
    for page in pages:
        text = page["text"]
        page_num = page["page_number"]
        
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end]
            
            heading = extract_section_heading(chunk_text)
            if heading != "Unknown Section":
                current_section = heading
                
            embedding = await generate_embedding(chunk_text)
            
            is_toc = False
            if current_section and any(t in current_section.lower() for t in ["table of contents", "contents", "index"]):
                is_toc = True
            elif "..." in chunk_text[:50] or re.search(r'\.{5,}', chunk_text):
                is_toc = True
                
            chunks.append({
                "chunk_id": f"{doc_id}_{chunk_index}",
                "chunk_index": chunk_index,
                "document_id": doc_id,
                "document_title": doc_title,
                "page_number": page_num,
                "section_heading": current_section,
                "text_content": chunk_text,
                "embedding": embedding,
                "is_table_of_contents": is_toc
            })
            chunk_index += 1
            start += (chunk_size - overlap)
            
    if chunks:
        await db.db.document_chunks.insert_many(chunks)
        # Create text index on document_chunks if it doesn't exist
        await db.db.document_chunks.create_index([("text_content", "text")])
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

def extract_groundwater_measurements(text: str, filename: str) -> List[dict]:
    """Parse document text for structured groundwater measurement metrics (district, depth, season, year)."""
    if not text:
        return []
        
    records = []
    known_districts = ["salem", "vellore", "chennai", "coimbatore", "madurai", "thanjavur", "ranipet", "tiruppur", "erode", "namakkal", "dindigul", "karur"]
    seen_keys = set()
    
    for line in text.splitlines():
        lower_l = line.lower()
        for dist in known_districts:
            if dist in lower_l:
                key = f"{dist}_{line[:30]}"
                if key in seen_keys:
                    continue
                seen_keys.add(key)
                
                depth_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:m\s*bgl|meters|m|depth)', line, re.IGNORECASE)
                if not depth_match:
                    continue
                depth_val = float(depth_match.group(1))
                
                season = "Post-Monsoon" if any(s in lower_l for s in ["post", "nov", "dec", "winter"]) else "Pre-Monsoon"
                year_match = re.search(r'\b(20\d\d)\b', line)
                year_val = int(year_match.group(1)) if year_match else 2026

                records.append({
                    "district": dist.title(),
                    "depth_m_bgl": depth_val,
                    "season": season,
                    "year": year_val,
                    "source_file": filename,
                    "raw_snippet": line.strip()[:180]
                })
                break
                
    return records

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
        
    # Check if duplicate file already exists for this user
    existing_doc = await db.db.documents.find_one({
        "uploaded_by": current_user["email"],
        "filename": file.filename
    })
    if existing_doc:
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate Upload Restricted: A document named '{file.filename}' has already been uploaded."
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
    MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB limit
    if file_size > MAX_FILE_SIZE:
        target_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=400,
            detail=f"File size ({file_size / (1024*1024):.1f}MB) exceeds the maximum allowed limit of 20MB."
        )

    pages = extract_text_from_file(target_path, file_ext)
    extracted_text = "\n".join([p["text"] for p in pages])

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
    doc_id_str = str(res.inserted_id)
    document_doc["_id"] = res.inserted_id
    
    # Process document chunks for vector search
    import asyncio
    asyncio.create_task(process_document_chunks(pages, doc_id_str, doc_title))
    
    # Extract structured groundwater measurement records
    measurements = extract_groundwater_measurements(extracted_text, file.filename)
    if measurements:
        await db.db.groundwater_records.insert_many(measurements)
    
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
        await db.db.knowledge_base.update_one(
            {"source": f"Uploaded File: {file.filename}"},
            {"$set": kb_entry},
            upsert=True
        )
    
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
            
    # Delete from documents collection and corresponding Knowledge Base entry
    await db.db.documents.delete_one({"_id": obj_id})
    if doc.get("filename"):
        await db.db.knowledge_base.delete_many({"source": f"Uploaded File: {doc.get('filename')}"})
    
    return APIResponse(
        success=True,
        message="Document deleted successfully",
        data={"doc_id": doc_id}
    )

