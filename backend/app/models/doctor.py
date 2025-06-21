"""
Doctor and Related Models
"""
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text, JSON, ForeignKey, Numeric, Integer, Float, Table
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.config.database import Base

class DoctorStatus(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class DoctorType(enum.Enum):
    GENERAL_PRACTITIONER = "general_practitioner"
    SPECIALIST = "specialist"
    CONSULTANT = "consultant"

class ConsultationType(enum.Enum):
    IN_PERSON = "in_person"
    VIDEO = "video"
    CHAT = "chat"
    HOME_VISIT = "home_visit"

class Doctor(Base):
    """نموذج الطبيب"""
    __tablename__ = "doctors"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    
    # معلومات أساسية
    title = Column(String(50), nullable=False)  # مثل "د." أو "أ.د."
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    gender = Column(String(20), nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    nationality = Column(String(100), nullable=False)
    
    # معلومات الاتصال
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=False)
    languages = Column(ARRAY(String), nullable=False)
    
    # المؤهلات والتراخيص
    medical_degree = Column(String(255), nullable=False)
    medical_school = Column(String(255), nullable=False)
    graduation_year = Column(Integer, nullable=False)
    license_number = Column(String(100), nullable=False, unique=True)
    license_expiry = Column(DateTime(timezone=True), nullable=False)
    
    # التخصص والخبرة
    type = Column(Enum(DoctorType), nullable=False)
    years_of_experience = Column(Integer, nullable=False)
    specializations = Column(ARRAY(String), nullable=False)
    sub_specializations = Column(ARRAY(String), nullable=True)
    certifications = Column(ARRAY(String), nullable=True)
    
    # معلومات العمل
    consultation_types = Column(ARRAY(Enum(ConsultationType)), nullable=False)
    consultation_duration = Column(Integer, default=30)  # بالدقائق
    max_patients_per_day = Column(Integer, default=20)
    accepting_new_patients = Column(Boolean, default=True)
    
    # الأسعار
    consultation_fees = Column(JSON, nullable=False)  # {"in_person": 100, "video": 80, "chat": 50}
    follow_up_fees = Column(JSON, nullable=False)
    emergency_fees = Column(JSON, nullable=True)
    insurance_providers = Column(ARRAY(String), nullable=True)
    
    # السيرة الذاتية والوصف
    bio = Column(Text, nullable=False)
    expertise_areas = Column(ARRAY(String), nullable=False)
    research_interests = Column(ARRAY(String), nullable=True)
    publications = Column(ARRAY(String), nullable=True)
    awards = Column(ARRAY(String), nullable=True)
    
    # الوسائط
    profile_image = Column(String(255), nullable=True)
    additional_images = Column(ARRAY(String), nullable=True)
    video_intro = Column(String(255), nullable=True)
    
    # التقييمات والمراجعات
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    total_patients = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    
    # الحالة والتحقق
    status = Column(Enum(DoctorStatus), default=DoctorStatus.PENDING_VERIFICATION)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    verified_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # الطوابع الزمنية
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    # العلاقات
    user = relationship("User", foreign_keys=[user_id])
    verifier = relationship("User", foreign_keys=[verified_by])
    clinics = relationship("DoctorClinic", back_populates="doctor")
    hospital_affiliations = relationship("DoctorHospital", back_populates="doctor")
    availability = relationship("DoctorAvailability", back_populates="doctor")
    reviews = relationship("DoctorReview", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")

class DoctorClinic(Base):
    """نموذج عيادة الطبيب"""
    __tablename__ = "doctor_clinics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    
    # معلومات العيادة
    name = Column(String(255), nullable=False)
    branch = Column(String(100), nullable=True)
    
    # العنوان
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=True)
    
    # الموقع الجغرافي
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # معلومات الاتصال
    phone = Column(String(20), nullable=False)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # ساعات العمل
    working_hours = Column(JSON, nullable=False)  # {"monday": {"start": "09:00", "end": "17:00"}, ...}
    breaks = Column(JSON, nullable=True)  # {"lunch": {"start": "13:00", "end": "14:00"}}
    
    # المرافق والخدمات
    facilities = Column(ARRAY(String), nullable=True)  # ["parking", "wheelchair_access", "lab"]
    services = Column(ARRAY(String), nullable=True)
    payment_methods = Column(ARRAY(String), nullable=False)
    insurance_accepted = Column(Boolean, default=True)
    
    # الوسائط
    images = Column(ARRAY(String), nullable=True)
    virtual_tour = Column(String(255), nullable=True)
    
    # الحالة
    is_primary = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    
    # الطوابع الزمنية
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    doctor = relationship("Doctor", back_populates="clinics")

class Hospital(Base):
    """نموذج المستشفى"""
    __tablename__ = "hospitals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # معلومات أساسية
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=False)  # حكومي، خاص، تعليمي
    established_year = Column(Integer, nullable=True)
    
    # العنوان
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=True)
    
    # الموقع الجغرافي
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # معلومات الاتصال
    phone = Column(String(20), nullable=False)
    emergency_phone = Column(String(20), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    
    # المعلومات الطبية
    bed_capacity = Column(Integer, nullable=True)
    icu_beds = Column(Integer, nullable=True)
    operating_rooms = Column(Integer, nullable=True)
    departments = Column(ARRAY(String), nullable=False)
    specialties = Column(ARRAY(String), nullable=False)
    facilities = Column(ARRAY(String), nullable=False)
    services = Column(ARRAY(String), nullable=False)
    
    # الطاقم الطبي
    doctors_count = Column(Integer, default=0)
    nurses_count = Column(Integer, default=0)
    staff_count = Column(Integer, default=0)
    
    # الاعتمادات والتراخيص
    accreditations = Column(ARRAY(String), nullable=True)
    certifications = Column(ARRAY(String), nullable=True)
    license_number = Column(String(100), nullable=False, unique=True)
    license_expiry = Column(DateTime(timezone=True), nullable=False)
    
    # التأمين والدفع
    insurance_providers = Column(ARRAY(String), nullable=True)
    payment_methods = Column(ARRAY(String), nullable=False)
    
    # التقييمات
    rating = Column(Float, default=0.0)
    total_reviews = Column(Integer, default=0)
    
    # الوسائط
    images = Column(ARRAY(String), nullable=True)
    virtual_tour = Column(String(255), nullable=True)
    logo = Column(String(255), nullable=True)
    
    # الحالة
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True), nullable=True)
    
    # الطوابع الزمنية
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    doctor_affiliations = relationship("DoctorHospital", back_populates="hospital")

class DoctorHospital(Base):
    """نموذج علاقة الطبيب بالمستشفى"""
    __tablename__ = "doctor_hospitals"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    hospital_id = Column(UUID(as_uuid=True), ForeignKey("hospitals.id"), nullable=False)
    
    # تفاصيل العمل
    department = Column(String(100), nullable=False)
    position = Column(String(100), nullable=False)
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    
    # نوع العمل
    is_primary = Column(Boolean, default=False)
    is_visiting = Column(Boolean, default=False)
    working_days = Column(ARRAY(String), nullable=False)
    
    # ساعات العمل
    working_hours = Column(JSON, nullable=False)
    on_call_availability = Column(Boolean, default=False)
    
    # الحالة
    is_active = Column(Boolean, default=True)
    
    # الطوابع الزمنية
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    doctor = relationship("Doctor", back_populates="hospital_affiliations")
    hospital = relationship("Hospital", back_populates="doctor_affiliations")

class DoctorReview(Base):
    """نموذج تقييم الطبيب"""
    __tablename__ = "doctor_reviews"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey("doctors.id"), nullable=False)
    patient_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=True)
    
    # التقييم
    rating = Column(Float, nullable=False)  # 1-5
    review = Column(Text, nullable=True)
    
    # تفاصيل التقييم
    waiting_time_rating = Column(Float, nullable=True)
    cleanliness_rating = Column(Float, nullable=True)
    staff_rating = Column(Float, nullable=True)
    communication_rating = Column(Float, nullable=True)
    value_rating = Column(Float, nullable=True)
    
    # التوصيات
    would_recommend = Column(Boolean, nullable=True)
    tags = Column(ARRAY(String), nullable=True)  # ["professional", "friendly", "knowledgeable"]
    
    # الحالة
    is_verified = Column(Boolean, default=False)
    is_public = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)
    
    # الطوابع الزمنية
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # العلاقات
    doctor = relationship("Doctor", back_populates="reviews")
    patient = relationship("User", foreign_keys=[patient_id])
    appointment = relationship("Appointment")
