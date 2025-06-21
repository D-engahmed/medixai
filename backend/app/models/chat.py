"""
Chat model and related models
"""
from enum import Enum
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.config.database import Base

class ChatType(str, Enum):
    GENERAL = "GENERAL"
    MEDICAL = "MEDICAL"
    EMERGENCY = "EMERGENCY"

class MessageType(str, Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    FILE = "FILE"
    SYSTEM = "SYSTEM"

class ChatStatus(str, Enum):
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"

class ChatSession(Base):
    """Chat session model"""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=True)
    chat_type = Column(SQLEnum(ChatType), nullable=False)
    status = Column(SQLEnum(ChatStatus), default=ChatStatus.ACTIVE)
    title = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    context = Column(JSON, default=dict)
    metadata = Column(JSON, default=dict)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="chat_sessions")
    doctor = relationship("Doctor")
    messages = relationship("ChatMessage", back_populates="session")
    escalations = relationship("ChatEscalation", back_populates="session")

    def __repr__(self):
        return f"<ChatSession {self.id}>"

class ChatMessage(Base):
    """Chat message model"""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    sender_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    message_type = Column(SQLEnum(MessageType), nullable=False)
    content = Column(Text, nullable=False)
    metadata = Column(JSON, default=dict)
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    sender = relationship("User")
    attachments = relationship("ChatAttachment", back_populates="message")

    def __repr__(self):
        return f"<ChatMessage {self.id}>"

class ChatAttachment(Base):
    """Chat attachment model"""
    __tablename__ = "chat_attachments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message_id = Column(String(36), ForeignKey("chat_messages.id"), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_url = Column(String(255), nullable=False)
    thumbnail_url = Column(String(255), nullable=True)
    metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")

    def __repr__(self):
        return f"<ChatAttachment {self.id}>"

class ChatEscalation(Base):
    """Chat escalation model"""
    __tablename__ = "chat_escalations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    triggered_by_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    assigned_to_id = Column(String(36), ForeignKey("doctors.id"), nullable=True)
    reason = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH, URGENT
    status = Column(String(20), nullable=False)  # PENDING, ASSIGNED, RESOLVED
    resolution = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    session = relationship("ChatSession", back_populates="escalations")
    triggered_by = relationship("User", foreign_keys=[triggered_by_id])
    assigned_to = relationship("Doctor", foreign_keys=[assigned_to_id])

    def __repr__(self):
        return f"<ChatEscalation {self.id}>"

class ChatBot(Base):
    """Chat bot model"""
    __tablename__ = "chat_bots"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    configuration = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ChatBot {self.name}>"

class ChatBotTraining(Base):
    """Chat bot training model"""
    __tablename__ = "chat_bot_training"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bot_id = Column(String(36), ForeignKey("chat_bots.id"), nullable=False)
    training_data = Column(JSON, nullable=False)
    metrics = Column(JSON, default=dict)
    status = Column(String(20), nullable=False)  # PENDING, IN_PROGRESS, COMPLETED, FAILED
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bot = relationship("ChatBot")

    def __repr__(self):
        return f"<ChatBotTraining {self.id}>"
