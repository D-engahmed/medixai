"""
Appointment System Models
"""
from datetime import datetime, time
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, JSON, Time, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
import uuid
from enum import Enum

from app.config.database import Base
from app.schemas.appointment import AppointmentStatus, AppointmentType, PaymentStatus

class AppointmentStatus(str, Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"

class AppointmentType(str, Enum):
    IN_PERSON = "IN_PERSON"
    VIDEO = "VIDEO"
    PHONE = "PHONE"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    FAILED = "FAILED"

class Appointment(Base):
    """نموذج الموعد في قاعدة البيانات"""
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_type = Column(String, nullable=False)
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, nullable=False)
    reason = Column(String, nullable=False)
    notes = Column(String)
    virtual_meeting_link = Column(String)
    symptoms = Column(ARRAY(String))
    medical_history_required = Column(Boolean, default=False)
    insurance_required = Column(Boolean, default=False)
    fee = Column(Float, nullable=False)
    status = Column(String, nullable=False, default=AppointmentStatus.PENDING)
    payment_status = Column(String, nullable=False, default=PaymentStatus.PENDING)
    payment_id = Column(UUID(as_uuid=True))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    cancelled_at = Column(DateTime)
    cancellation_reason = Column(String)
    reminder_sent = Column(Boolean, default=False)
    feedback_submitted = Column(Boolean, default=False)

    # العلاقات
    doctor = relationship("User", foreign_keys=[doctor_id], back_populates="doctor_appointments")
    patient = relationship("User", foreign_keys=[patient_id], back_populates="patient_appointments")
    feedback = relationship("AppointmentFeedback", back_populates="appointment", uselist=False)
    reminders = relationship("AppointmentReminder", back_populates="appointment")
    notifications = relationship("AppointmentNotification", back_populates="appointment")

    # القيود
    __table_args__ = (
        CheckConstraint('duration_minutes >= 15 AND duration_minutes <= 180'),
        CheckConstraint('fee >= 0'),
        Index('ix_appointments_doctor_scheduled', 'doctor_id', 'scheduled_at'),
        Index('ix_appointments_patient_scheduled', 'patient_id', 'scheduled_at'),
        Index('ix_appointments_status_date', 'status', 'scheduled_at'),
    )

class AppointmentFeedback(Base):
    """نموذج تقييم الموعد في قاعدة البيانات"""
    __tablename__ = "appointment_feedbacks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False, unique=True)
    rating = Column(Integer, nullable=False)
    comments = Column(String)
    wait_time_rating = Column(Integer, nullable=False)
    doctor_rating = Column(Integer, nullable=False)
    facility_rating = Column(Integer, nullable=False)
    would_recommend = Column(Boolean, nullable=False)
    areas_of_improvement = Column(ARRAY(String))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    appointment = relationship("Appointment", back_populates="feedback")

    # القيود
    __table_args__ = (
        CheckConstraint('rating >= 1 AND rating <= 5'),
        CheckConstraint('wait_time_rating >= 1 AND wait_time_rating <= 5'),
        CheckConstraint('doctor_rating >= 1 AND doctor_rating <= 5'),
        CheckConstraint('facility_rating >= 1 AND facility_rating <= 5'),
    )

class DoctorSchedule(Base):
    """نموذج جدول الطبيب في قاعدة البيانات"""
    __tablename__ = "doctor_schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    date = Column(DateTime, nullable=False)
    time_slots = Column(JSONB, nullable=False)
    break_times = Column(JSONB, default=[])
    is_available = Column(Boolean, default=True)
    max_appointments = Column(Integer)
    appointment_duration = Column(Integer, default=30)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # العلاقات
    doctor = relationship("User", back_populates="schedules")

    # القيود
    __table_args__ = (
        Index('ix_doctor_schedules_date', 'doctor_id', 'date', unique=True),
        CheckConstraint('appointment_duration >= 15'),
    )

class AppointmentReminder(Base):
    """نموذج تذكير الموعد في قاعدة البيانات"""
    __tablename__ = "appointment_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    reminder_type = Column(String, nullable=False)  # email, sms, push
    scheduled_time = Column(DateTime, nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="pending")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime)

    # العلاقات
    appointment = relationship("Appointment", back_populates="reminders")
    recipient = relationship("User")

    # القيود
    __table_args__ = (
        Index('ix_appointment_reminders_scheduled', 'scheduled_time', 'status'),
    )

class AppointmentNotification(Base):
    """نموذج إشعارات المواعيد في قاعدة البيانات"""
    __tablename__ = "appointment_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    notification_type = Column(String, nullable=False)
    recipient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    message = Column(String, nullable=False)
    status = Column(String, default="pending")
    scheduled_time = Column(DateTime)
    metadata = Column(JSONB, default={})
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sent_at = Column(DateTime)

    # العلاقات
    appointment = relationship("Appointment", back_populates="notifications")
    recipient = relationship("User")

    # القيود
    __table_args__ = (
        Index('ix_appointment_notifications_status', 'status', 'scheduled_time'),
    )
