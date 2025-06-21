"""
Chat schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

from app.models.chat import ChatType, ChatStatus, MessageRole

class ChatSessionBase(BaseModel):
    """Base chat session schema"""
    chat_type: ChatType
    initial_context: Optional[Dict[str, Any]] = None

class ChatSessionCreate(ChatSessionBase):
    """Chat session creation schema"""
    pass

class ChatSessionResponse(ChatSessionBase):
    """Chat session response schema"""
    id: UUID
    patient_id: UUID
    status: ChatStatus
    context: Dict[str, Any] = {}
    symptoms: List[str] = []
    medical_history: Dict[str, Any] = {}
    relevant_documents: List[UUID] = []
    confidence_score: float = 0.0
    started_at: datetime
    ended_at: Optional[datetime] = None
    last_message_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessageBase(BaseModel):
    """Base chat message schema"""
    content: str = Field(..., max_length=4096)
    metadata: Optional[Dict[str, Any]] = None

class ChatMessageCreate(ChatMessageBase):
    """Chat message creation schema"""
    role: MessageRole = MessageRole.USER

class ChatMessageResponse(ChatMessageBase):
    """Chat message response schema"""
    id: UUID
    session_id: UUID
    role: MessageRole
    tokens_used: int = 0
    citations: List[Dict[str, Any]] = []
    confidence_score: float = 0.0
    requires_escalation: bool = False
    escalation_reason: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class ChatEscalationBase(BaseModel):
    """Base chat escalation schema"""
    reason: str
    doctor_notes: Optional[str] = None

class ChatEscalationCreate(ChatEscalationBase):
    """Chat escalation creation schema"""
    pass

class ChatEscalationResponse(ChatEscalationBase):
    """Chat escalation response schema"""
    id: UUID
    session_id: UUID
    doctor_id: Optional[UUID] = None
    trigger_message_id: UUID
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class MedicalReferenceBase(BaseModel):
    """Base medical reference schema"""
    title: str = Field(..., max_length=255)
    content: str
    source: str = Field(..., max_length=255)
    source_url: Optional[str] = Field(None, max_length=512)
    category: str = Field(..., max_length=100)
    tags: List[str] = []

class MedicalReferenceCreate(MedicalReferenceBase):
    """Medical reference creation schema"""
    pass

class MedicalReferenceResponse(MedicalReferenceBase):
    """Medical reference response schema"""
    id: UUID
    is_verified: bool = False
    verified_by: Optional[UUID] = None
    verification_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True 