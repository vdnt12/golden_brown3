from typing import Optional, Literal
from pydantic import BaseModel, Field
import time

class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    status: Literal["processing", "ready", "failed"] = "processing"
    pages: Optional[int] = 0
    chunks: Optional[int] = 0
    error: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    pages: Optional[int] = None
    chunks: Optional[int] = None
    error: Optional[str] = None

class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    status: str

class ExtractedPage(BaseModel):
    page_number: int
    text: str
    is_ocr: bool = False

class DocumentChunk(BaseModel):
    chunk_id: str
    document_id: str
    filename: str
    page: Optional[int] = None
    chunk_index: int
    text: str

class SummarizeRequest(BaseModel):
    document_id: Optional[str] = None

class SummarizeResponse(BaseModel):
    document_id: str
    summary: str
    status: str
    message: Optional[str] = None
    total_chunks_processed: Optional[int] = None

