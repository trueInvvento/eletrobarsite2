from uuid import UUID

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: UUID | None = None
    visitor_id: str | None = Field(None, max_length=128)


class ChatResponse(BaseModel):
    session_id: UUID
    reply: str


class LeadRequest(BaseModel):
    session_id: UUID
    contact: str | None = Field(None, max_length=256)


class LeadResponse(BaseModel):
    ok: bool
    message: str


class IngestDocument(BaseModel):
    source: str
    title: str
    content: str
    metadata: dict = Field(default_factory=dict)


class HealthResponse(BaseModel):
    status: str
    database: bool
