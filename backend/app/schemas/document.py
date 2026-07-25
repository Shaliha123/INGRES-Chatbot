from typing import Optional
from pydantic import BaseModel

class DocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    file_size_bytes: int
    uploaded_by: str
    upload_date: str
    extracted_text_preview: Optional[str] = ""
    storage_path: str
