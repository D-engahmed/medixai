"""
Doctor Dashboard Schemas
"""
from typing import List, Optional, Dict
from datetime import datetime, date
from uuid import UUID
from pydantic import BaseModel, conint, confloat

class AppointmentStats(BaseModel):
    """إحصائيات المواعيد"""
    total: int
    completed: int
    cancelled: int
    upcoming: int
    completion_rate: float
    cancellation_rate: float
    avg_duration: float

class RevenueStats(BaseModel):
    """إحصائيات الإيرادات"""
    total_revenue: float
    current_month: float
    last_month: float
    growth_rate: float
    by_service: Dict[str, float]
    by_month: Dict[str, float]

class PatientStats(BaseModel):
    """إحصائيات المرضى"""
    total_patients: int
    new_patients: int
    returning_patients: int
    retention_rate: float
    satisfaction_rate: float
    avg_rating: float
    demographics: Dict[str, int]

class TreatmentStats(BaseModel):
    """إحصائيات العلاج"""
    total_treatments: int
    success_rate: float
    common_conditions: Dict[str, int]
    avg_recovery_time: float
    medication_effectiveness: Dict[str, float]

class ChatStats(BaseModel):
    """إحصائيات المحادثات"""
    total_chats: int
    avg_response_time: float
    satisfaction_rate: float
    common_topics: Dict[str, int]
    escalation_rate: float

class DailySchedule(BaseModel):
    """الجدول اليومي"""
    date: date
    appointments: List[Dict]
    available_slots: List[Dict]
    breaks: List[Dict]
    total_hours: float

class DashboardOverview(BaseModel):
    """نظرة عامة على لوحة التحكم"""
    appointment_stats: AppointmentStats
    revenue_stats: RevenueStats
    patient_stats: PatientStats
    treatment_stats: TreatmentStats
    chat_stats: ChatStats
    today_schedule: DailySchedule

class TimeRange(BaseModel):
    """نطاق زمني"""
    start_date: date
    end_date: date

class DashboardFilter(BaseModel):
    """فلتر لوحة التحكم"""
    time_range: Optional[TimeRange]
    service_types: Optional[List[str]]
    patient_groups: Optional[List[str]]
    conditions: Optional[List[str]]
    locations: Optional[List[str]]

class PerformanceMetric(BaseModel):
    """مقياس الأداء"""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend: List[float]
    benchmark: Optional[float]

class Alert(BaseModel):
    """تنبيه"""
    id: UUID
    type: str
    message: str
    severity: str
    created_at: datetime
    is_read: bool
    action_required: bool
    link: Optional[str]

class DashboardResponse(BaseModel):
    """استجابة لوحة التحكم"""
    overview: DashboardOverview
    performance_metrics: List[PerformanceMetric]
    alerts: List[Alert]
    last_updated: datetime 