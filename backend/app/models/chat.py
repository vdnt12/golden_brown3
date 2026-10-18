from typing import List, Optional
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str

class ChatRequest(BaseModel):
    document_id: str
    question: str
    conversation: List[ChatMessage] = Field(default_factory=list)

class ChatSource(BaseModel):
    filename: str
    page: Optional[int] = None
    chunk_id: str

class ChatResponse(BaseModel):
    answer: str
    sources: List[ChatSource] = Field(default_factory=list)
