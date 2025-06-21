"""
Follow-Up System Models
"""
from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

from app.config.database import Base

class Interaction(Base):
    """نموذج التفاعل في قاعدة البيانات"""
    __tablename__ = "interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    metadata = Column(JSONB, default={})
    timestamp = Column(DateTime, nullable=False)
    status = Column(String, nullable=False)
    importance = Column(Integer, nullable=False)
    requires_action = Column(Boolean, default=False)
    action_by = Column(DateTime)
    
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    reference_id = Column(UUID(as_uuid=True))
    reference_type = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_interactions")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_interactions")

    # الفهارس
    __table_args__ = (
        Index("ix_interactions_patient_timestamp", "patient_id", "timestamp"),
        Index("ix_interactions_doctor_timestamp", "doctor_id", "timestamp"),
        Index("ix_interactions_reference", "reference_id", "reference_type"),
        Index("ix_interactions_type_status", "type", "status"),
    )

class FollowUpRule(Base):
    """نموذج قواعد المتابعة"""
    __tablename__ = "follow_up_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    description = Column(String)
    trigger_type = Column(String, nullable=False)  # appointment, prescription, etc.
    conditions = Column(JSONB, nullable=False)  # شروط تفعيل القاعدة
    actions = Column(JSONB, nullable=False)  # الإجراءات المطلوبة
    priority = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # الفهارس
    __table_args__ = (
        Index("ix_follow_up_rules_trigger", "trigger_type", "is_active"),
    )

class HealthMetric(Base):
    """نموذج المقاييس الصحية"""
    __tablename__ = "health_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    metric_type = Column(String, nullable=False)  # blood_pressure, weight, etc.
    value = Column(JSONB, nullable=False)
    unit = Column(String)
    timestamp = Column(DateTime, nullable=False)
    source = Column(String)  # manual, device, lab, etc.
    notes = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    patient = relationship("User", back_populates="health_metrics")

    # الفهارس
    __table_args__ = (
        Index("ix_health_metrics_patient_type", "patient_id", "metric_type"),
        Index("ix_health_metrics_timestamp", "timestamp"),
    )

class TreatmentPlan(Base):
    """نموذج خطة العلاج"""
    __tablename__ = "treatment_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(String)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime)
    status = Column(String, nullable=False)
    goals = Column(JSONB, default=[])
    instructions = Column(JSONB, default={})
    progress = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    patient = relationship("User", foreign_keys=[patient_id], back_populates="treatment_plans")
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="created_treatment_plans")

    # الفهارس
    __table_args__ = (
        Index("ix_treatment_plans_patient", "patient_id", "status"),
        Index("ix_treatment_plans_doctor", "doctor_id", "status"),
    )

class FollowUpStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    MISSED = "MISSED"

class FollowUpType(str, Enum):
    GENERAL = "GENERAL"
    POST_SURGERY = "POST_SURGERY"
    MEDICATION = "MEDICATION"
    CHRONIC = "CHRONIC"
    REHABILITATION = "REHABILITATION"

class FollowUp(Base):
    """Follow-up model"""
    __tablename__ = "follow_ups"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    follow_up_type = Column(SQLEnum(FollowUpType), nullable=False)
    status = Column(SQLEnum(FollowUpStatus), default=FollowUpStatus.SCHEDULED)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_date = Column(DateTime, nullable=False)
    completed_date = Column(DateTime, nullable=True)
    duration_days = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)
    goals = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    doctor = relationship("Doctor")
    appointment = relationship("Appointment")
    tasks = relationship("FollowUpTask", back_populates="follow_up")
    progress = relationship("FollowUpProgress", back_populates="follow_up")
    reminders = relationship("FollowUpReminder", back_populates="follow_up")

    def __repr__(self):
        return f"<FollowUp {self.id}>"

class FollowUpTask(Base):
    """Follow-up task model"""
    __tablename__ = "follow_up_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    follow_up_id = Column(String(36), ForeignKey("follow_ups.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=False)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)
    priority = Column(String(20), nullable=False)  # LOW, MEDIUM, HIGH
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    follow_up = relationship("FollowUp", back_populates="tasks")

    def __repr__(self):
        return f"<FollowUpTask {self.id}>"

class FollowUpProgress(Base):
    """Follow-up progress model"""
    __tablename__ = "follow_up_progress"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    follow_up_id = Column(String(36), ForeignKey("follow_ups.id"), nullable=False)
    recorded_by_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    metrics = Column(JSON, nullable=False)
    notes = Column(Text, nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    follow_up = relationship("FollowUp", back_populates="progress")
    recorded_by = relationship("User")

    def __repr__(self):
        return f"<FollowUpProgress {self.id}>"

class FollowUpReminder(Base):
    """Follow-up reminder model"""
    __tablename__ = "follow_up_reminders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    follow_up_id = Column(String(36), ForeignKey("follow_ups.id"), nullable=False)
    recipient_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    reminder_type = Column(String(20), nullable=False)  # EMAIL, SMS, PUSH
    scheduled_at = Column(DateTime, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    status = Column(String(20), default="PENDING")  # PENDING, SENT, FAILED
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    follow_up = relationship("FollowUp", back_populates="reminders")
    recipient = relationship("User")

    def __repr__(self):
        return f"<FollowUpReminder {self.id}>"

class FollowUpTemplate(Base):
    """Follow-up template model"""
    __tablename__ = "follow_up_templates"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    follow_up_type = Column(SQLEnum(FollowUpType), nullable=False)
    duration_days = Column(Integer, nullable=False)
    tasks = Column(JSON, default=list)
    metrics = Column(JSON, default=dict)
    instructions = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<FollowUpTemplate {self.name}>"

class MedicalRecord(Base):
    """Medical record model"""
    __tablename__ = "medical_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    record_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    diagnosis = Column(JSON, default=list)
    treatment = Column(JSON, default=list)
    attachments = Column(JSON, default=list)
    is_confidential = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="medical_records")
    doctor = relationship("Doctor")

    def __repr__(self):
        return f"<MedicalRecord {self.id}>" 