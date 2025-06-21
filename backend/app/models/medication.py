"""
Medication model and related models
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.config.database import Base

class MedicationType(str, Enum):
    TABLET = "TABLET"
    CAPSULE = "CAPSULE"
    LIQUID = "LIQUID"
    INJECTION = "INJECTION"
    CREAM = "CREAM"
    OINTMENT = "OINTMENT"
    DROPS = "DROPS"
    INHALER = "INHALER"
    PATCH = "PATCH"
    OTHER = "OTHER"

class PrescriptionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

class Medication(Base):
    """Medication model"""
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=True)
    manufacturer = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    medication_type = Column(SQLEnum(MedicationType), nullable=False)
    dosage_form = Column(String(50), nullable=False)
    strength = Column(String(50), nullable=False)
    package_size = Column(String(50), nullable=True)
    price = Column(Float, nullable=False)
    requires_prescription = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    stock_quantity = Column(Integer, default=0)
    reorder_level = Column(Integer, default=10)
    side_effects = Column(JSON, default=list)
    contraindications = Column(JSON, default=list)
    storage_instructions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prescriptions = relationship("Prescription", back_populates="medication")
    orders = relationship("MedicationOrder", back_populates="medication")
    interactions = relationship("DrugInteraction", back_populates="medication")

    def __repr__(self):
        return f"<Medication {self.name}>"

class Prescription(Base):
    """Prescription model"""
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(String(36), ForeignKey("doctors.id"), nullable=False)
    appointment_id = Column(String(36), ForeignKey("appointments.id"), nullable=True)
    medication_id = Column(String(36), ForeignKey("medications.id"), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    duration_days = Column(Integer, nullable=False)
    quantity = Column(Integer, nullable=False)
    instructions = Column(Text, nullable=True)
    status = Column(SQLEnum(PrescriptionStatus), default=PrescriptionStatus.ACTIVE)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient", back_populates="prescriptions")
    doctor = relationship("Doctor", back_populates="prescriptions")
    appointment = relationship("Appointment", back_populates="prescription")
    medication = relationship("Medication", back_populates="prescriptions")
    refills = relationship("PrescriptionRefill", back_populates="prescription")

    def __repr__(self):
        return f"<Prescription {self.id}>"

class PrescriptionRefill(Base):
    """Prescription refill model"""
    __tablename__ = "prescription_refills"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    prescription_id = Column(String(36), ForeignKey("prescriptions.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    refill_date = Column(DateTime, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    prescription = relationship("Prescription", back_populates="refills")

    def __repr__(self):
        return f"<PrescriptionRefill {self.id}>"

class DrugInteraction(Base):
    """Drug interaction model"""
    __tablename__ = "drug_interactions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    medication_id = Column(String(36), ForeignKey("medications.id"), nullable=False)
    interacts_with_id = Column(String(36), ForeignKey("medications.id"), nullable=False)
    severity = Column(String(20), nullable=False)  # MINOR, MODERATE, MAJOR
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication = relationship("Medication", foreign_keys=[medication_id], back_populates="interactions")
    interacts_with = relationship("Medication", foreign_keys=[interacts_with_id])

    def __repr__(self):
        return f"<DrugInteraction {self.id}>"

class MedicationOrder(Base):
    """Medication order model"""
    __tablename__ = "medication_orders"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patients.id"), nullable=False)
    medication_id = Column(String(36), ForeignKey("medications.id"), nullable=False)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id"), nullable=True)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Float, nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    payment_id = Column(String(36), nullable=True)
    shipping_address = Column(JSON, default=dict)
    tracking_number = Column(String(100), nullable=True)
    status = Column(String(20), nullable=False)  # PENDING, PROCESSING, SHIPPED, DELIVERED
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    patient = relationship("Patient")
    medication = relationship("Medication", back_populates="orders")
    prescription = relationship("Prescription")

    def __repr__(self):
        return f"<MedicationOrder {self.id}>"

class MedicationInventory(Base):
    """Medication inventory model"""
    __tablename__ = "medication_inventory"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    medication_id = Column(String(36), ForeignKey("medications.id"), nullable=False)
    batch_number = Column(String(50), nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_cost = Column(Float, nullable=False)
    supplier = Column(String(255), nullable=True)
    purchase_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    medication = relationship("Medication")

    def __repr__(self):
        return f"<MedicationInventory {self.id}>"