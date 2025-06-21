"""
Doctor and Hospital Schemas
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, EmailStr, constr, confloat, conint, HttpUrl, Field
from enum import Enum

# Enums
from app.models.doctor import DoctorStatus, DoctorType, ConsultationType

class DistanceUnit(str, Enum):
    """وحدة قياس المسافة"""
    KM = "km"
    MILES = "miles"

class GeoLocation(BaseModel):
    """نموذج الموقع الجغرافي"""
    latitude: float = Field(..., ge=-90, le=90, description="خط العرض")
    longitude: float = Field(..., ge=-180, le=180, description="خط الطول")

class WorkingHours(BaseModel):
    """نموذج ساعات العمل"""
    start: str
    end: str
    is_closed: bool = False

class DaySchedule(BaseModel):
    """نموذج جدول اليوم"""
    working_hours: WorkingHours
    breaks: Optional[List[WorkingHours]] = None

class WeeklySchedule(BaseModel):
    """نموذج الجدول الأسبوعي"""
    monday: DaySchedule
    tuesday: DaySchedule
    wednesday: DaySchedule
    thursday: DaySchedule
    friday: DaySchedule
    saturday: Optional[DaySchedule]
    sunday: Optional[DaySchedule]

# Doctor Schemas
class DoctorBase(BaseModel):
    """النموذج الأساسي للطبيب"""
    title: str
    first_name: str
    last_name: str
    gender: str
    nationality: str
    languages: List[str]
    type: DoctorType
    specializations: List[str]
    consultation_types: List[ConsultationType]
    bio: str
    expertise_areas: List[str]

class DoctorCreate(DoctorBase):
    """نموذج إنشاء طبيب جديد"""
    email: EmailStr
    phone: str
    date_of_birth: datetime
    medical_degree: str
    medical_school: str
    graduation_year: conint(ge=1950, le=datetime.now().year)
    license_number: str
    license_expiry: datetime
    years_of_experience: conint(ge=0)
    consultation_duration: conint(ge=10, le=120)
    consultation_fees: dict
    follow_up_fees: dict

class DoctorUpdate(BaseModel):
    """نموذج تحديث بيانات الطبيب"""
    title: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    languages: Optional[List[str]] = None
    bio: Optional[str] = None
    expertise_areas: Optional[List[str]] = None
    consultation_types: Optional[List[ConsultationType]] = None
    consultation_duration: Optional[conint(ge=10, le=120)] = None
    consultation_fees: Optional[dict] = None
    follow_up_fees: Optional[dict] = None
    accepting_new_patients: Optional[bool] = None
    profile_image: Optional[HttpUrl] = None
    status: Optional[DoctorStatus] = None

class DoctorInDB(DoctorBase):
    """نموذج الطبيب في قاعدة البيانات"""
    id: UUID
    user_id: UUID
    email: EmailStr
    phone: str
    status: DoctorStatus
    is_verified: bool
    rating: float
    total_reviews: int
    total_patients: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class DoctorDistance(BaseModel):
    """نموذج المسافة للطبيب"""
    value: float
    unit: DistanceUnit
    text: str

class DoctorSearchParams(BaseModel):
    """نموذج معايير البحث عن الأطباء"""
    query: Optional[str] = None
    specialization: Optional[str] = None
    city: Optional[str] = None
    consultation_type: Optional[ConsultationType] = None
    min_rating: Optional[confloat(ge=0, le=5)] = None
    max_price: Optional[float] = None
    insurance_provider: Optional[str] = None
    language: Optional[str] = None
    gender: Optional[str] = None
    available_today: Optional[bool] = None
    location: Optional[GeoLocation] = None
    radius_km: Optional[confloat(gt=0)] = Field(
        default=10.0,
        description="نصف قطر البحث (الافتراضي: 10 كم)"
    )
    distance_unit: Optional[DistanceUnit] = Field(
        default=DistanceUnit.KM,
        description="وحدة قياس المسافة (كم/ميل)"
    )

class DoctorPublic(DoctorBase):
    """نموذج الطبيب العام"""
    id: UUID
    rating: float
    total_reviews: int
    total_patients: int
    profile_image: Optional[HttpUrl]
    consultation_types: List[ConsultationType]
    consultation_fees: dict
    distance: Optional[DoctorDistance] = None

    class Config:
        orm_mode = True

class DoctorDetail(DoctorPublic):
    """نموذج تفاصيل الطبيب"""
    medical_degree: str
    medical_school: str
    graduation_year: int
    years_of_experience: int
    sub_specializations: Optional[List[str]]
    certifications: Optional[List[str]]
    research_interests: Optional[List[str]]
    publications: Optional[List[str]]
    awards: Optional[List[str]]
    video_intro: Optional[HttpUrl]
    additional_images: Optional[List[HttpUrl]]

# Clinic Schemas
class ClinicBase(BaseModel):
    """النموذج الأساسي للعيادة"""
    name: str
    branch: Optional[str]
    address: str
    city: str
    state: str
    country: str
    postal_code: Optional[str]
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)
    phone: str
    email: Optional[EmailStr]
    website: Optional[HttpUrl]
    working_hours: WeeklySchedule
    facilities: Optional[List[str]]
    services: Optional[List[str]]
    payment_methods: List[str]
    insurance_accepted: bool

class ClinicCreate(ClinicBase):
    """نموذج إنشاء عيادة جديدة"""
    doctor_id: UUID
    is_primary: bool = False

class ClinicUpdate(BaseModel):
    """نموذج تحديث بيانات العيادة"""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    working_hours: Optional[WeeklySchedule] = None
    facilities: Optional[List[str]] = None
    services: Optional[List[str]] = None
    payment_methods: Optional[List[str]] = None
    insurance_accepted: Optional[bool] = None
    is_active: Optional[bool] = None

class ClinicInDB(ClinicBase):
    """نموذج العيادة في قاعدة البيانات"""
    id: UUID
    doctor_id: UUID
    is_primary: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Hospital Schemas
class HospitalBase(BaseModel):
    """النموذج الأساسي للمستشفى"""
    name: str
    type: str
    address: str
    city: str
    state: str
    country: str
    postal_code: Optional[str]
    latitude: confloat(ge=-90, le=90)
    longitude: confloat(ge=-180, le=180)
    phone: str
    emergency_phone: Optional[str]
    email: Optional[EmailStr]
    website: Optional[HttpUrl]
    departments: List[str]
    specialties: List[str]
    facilities: List[str]
    services: List[str]

class HospitalCreate(HospitalBase):
    """نموذج إنشاء مستشفى جديد"""
    established_year: Optional[int]
    bed_capacity: Optional[int]
    license_number: str
    license_expiry: datetime

class HospitalUpdate(BaseModel):
    """نموذج تحديث بيانات المستشفى"""
    name: Optional[str] = None
    phone: Optional[str] = None
    emergency_phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[HttpUrl] = None
    departments: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    facilities: Optional[List[str]] = None
    services: Optional[List[str]] = None
    bed_capacity: Optional[int] = None
    is_active: Optional[bool] = None

class HospitalInDB(HospitalBase):
    """نموذج المستشفى في قاعدة البيانات"""
    id: UUID
    established_year: Optional[int]
    bed_capacity: Optional[int]
    icu_beds: Optional[int]
    operating_rooms: Optional[int]
    doctors_count: int
    nurses_count: int
    staff_count: int
    rating: float
    total_reviews: int
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class HospitalPublic(HospitalBase):
    """نموذج المستشفى العام"""
    id: UUID
    established_year: Optional[int]
    bed_capacity: Optional[int]
    rating: float
    total_reviews: int
    images: Optional[List[HttpUrl]]
    logo: Optional[HttpUrl]

    class Config:
        orm_mode = True

# Doctor-Hospital Affiliation Schemas
class DoctorHospitalBase(BaseModel):
    """النموذج الأساسي لعلاقة الطبيب بالمستشفى"""
    department: str
    position: str
    start_date: datetime
    end_date: Optional[datetime]
    is_primary: bool
    is_visiting: bool
    working_days: List[str]
    working_hours: WeeklySchedule
    on_call_availability: bool

class DoctorHospitalCreate(DoctorHospitalBase):
    """نموذج إنشاء علاقة طبيب-مستشفى جديدة"""
    doctor_id: UUID
    hospital_id: UUID

class DoctorHospitalUpdate(BaseModel):
    """نموذج تحديث علاقة طبيب-مستشفى"""
    department: Optional[str] = None
    position: Optional[str] = None
    end_date: Optional[datetime] = None
    working_days: Optional[List[str]] = None
    working_hours: Optional[WeeklySchedule] = None
    on_call_availability: Optional[bool] = None
    is_active: Optional[bool] = None

class DoctorHospitalInDB(DoctorHospitalBase):
    """نموذج علاقة طبيب-مستشفى في قاعدة البيانات"""
    id: UUID
    doctor_id: UUID
    hospital_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Review Schemas
class ReviewBase(BaseModel):
    """النموذج الأساسي للتقييم"""
    rating: confloat(ge=1, le=5)
    review: Optional[str]
    waiting_time_rating: Optional[confloat(ge=1, le=5)]
    cleanliness_rating: Optional[confloat(ge=1, le=5)]
    staff_rating: Optional[confloat(ge=1, le=5)]
    communication_rating: Optional[confloat(ge=1, le=5)]
    value_rating: Optional[confloat(ge=1, le=5)]
    would_recommend: Optional[bool]
    tags: Optional[List[str]]
    is_anonymous: bool = False

class ReviewCreate(ReviewBase):
    """نموذج إنشاء تقييم جديد"""
    doctor_id: UUID
    appointment_id: Optional[UUID]

class ReviewUpdate(BaseModel):
    """نموذج تحديث التقييم"""
    rating: Optional[confloat(ge=1, le=5)] = None
    review: Optional[str] = None
    waiting_time_rating: Optional[confloat(ge=1, le=5)] = None
    cleanliness_rating: Optional[confloat(ge=1, le=5)] = None
    staff_rating: Optional[confloat(ge=1, le=5)] = None
    communication_rating: Optional[confloat(ge=1, le=5)] = None
    value_rating: Optional[confloat(ge=1, le=5)] = None
    would_recommend: Optional[bool] = None
    tags: Optional[List[str]] = None
    is_public: Optional[bool] = None

class ReviewInDB(ReviewBase):
    """نموذج التقييم في قاعدة البيانات"""
    id: UUID
    doctor_id: UUID
    patient_id: UUID
    appointment_id: Optional[UUID]
    is_verified: bool
    is_public: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# Search Schemas
class HospitalSearchParams(BaseModel):
    """نموذج معايير البحث عن المستشفيات"""
    query: Optional[str] = None
    type: Optional[str] = None
    city: Optional[str] = None
    specialty: Optional[str] = None
    min_rating: Optional[confloat(ge=0, le=5)] = None
    insurance_provider: Optional[str] = None
    has_emergency: Optional[bool] = None
    location: Optional[GeoLocation] = None
    radius_km: Optional[confloat(gt=0)] = None
