"""
Follow-Up System Schemas
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field

class InteractionType(str):
    APPOINTMENT = "appointment"
    CHAT = "chat"
    PRESCRIPTION = "prescription"
    MEDICATION = "medication"
    TEST_RESULT = "test_result"
    FOLLOW_UP = "follow_up"

class InteractionBase(BaseModel):
    """نموذج التفاعل الأساسي"""
    type: InteractionType
    title: str
    description: str
    metadata: Dict[str, Any]
    timestamp: datetime
    status: str
    importance: int = Field(ge=1, le=5)
    requires_action: bool = False
    action_by: Optional[datetime]

class InteractionCreate(InteractionBase):
    """نموذج إنشاء تفاعل"""
    patient_id: UUID
    doctor_id: Optional[UUID]
    reference_id: Optional[UUID]
    reference_type: Optional[str]

class InteractionUpdate(BaseModel):
    """نموذج تحديث تفاعل"""
    title: Optional[str]
    description: Optional[str]
    metadata: Optional[Dict[str, Any]]
    status: Optional[str]
    importance: Optional[int] = Field(ge=1, le=5)
    requires_action: Optional[bool]
    action_by: Optional[datetime]

class InteractionInDB(InteractionBase):
    """نموذج التفاعل في قاعدة البيانات"""
    id: UUID
    patient_id: UUID
    doctor_id: Optional[UUID]
    reference_id: Optional[UUID]
    reference_type: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class TimelineEntry(BaseModel):
    """نموذج عنصر الجدول الزمني"""
    date: datetime
    interactions: List[InteractionInDB]
    summary: str
    total_items: int
    has_critical: bool

class Timeline(BaseModel):
    """نموذج الجدول الزمني"""
    entries: List[TimelineEntry]
    total_interactions: int
    date_range: Dict[str, datetime]
    statistics: Dict[str, Any]

class AnalyticsPeriod(str):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"

class AnalyticsFilter(BaseModel):
    """نموذج فلتر التحليلات"""
    start_date: datetime
    end_date: datetime
    interaction_types: Optional[List[InteractionType]]
    period: AnalyticsPeriod = AnalyticsPeriod.MONTHLY
    include_metadata: bool = False

class AnalyticsSummary(BaseModel):
    """نموذج ملخص التحليلات"""
    total_interactions: int
    interaction_types_count: Dict[str, int]
    average_importance: float
    completion_rate: float
    response_times: Dict[str, float]
    trends: Dict[str, List[float]]
    common_patterns: List[Dict[str, Any]]

class PatientSummary(BaseModel):
    """نموذج ملخص المريض"""
    total_visits: int
    last_visit: datetime
    upcoming_appointments: int
    active_prescriptions: int
    compliance_rate: float
    risk_factors: List[str]
    recent_interactions: List[InteractionInDB]
    health_trends: Dict[str, List[float]]

class DoctorSummary(BaseModel):
    """نموذج ملخص الطبيب"""
    total_patients: int
    active_cases: int
    follow_up_rate: float
    average_visit_interval: float
    treatment_outcomes: Dict[str, float]
    patient_satisfaction: float
    workload_distribution: Dict[str, int] 