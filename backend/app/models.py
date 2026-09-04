from typing import Literal
from pydantic import BaseModel, Field

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=4000)
    conversation_id: str | None = None
    document_ids: list[str] = []
    history: list[ChatMessage] = []

class Citation(BaseModel):
    number: int
    document_id: str
    filename: str
    page: int | None = None
    excerpt: str
    score: float

class ChatResponse(BaseModel):
    answer: str
    agent: str
    conversation_id: str
    citations: list[Citation]

class DocumentInfo(BaseModel):
    id: str
    filename: str
    chunks: int
    category: str

