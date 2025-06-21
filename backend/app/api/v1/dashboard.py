"""
Doctor Dashboard API Endpoints
"""
from typing import List, Optional
from datetime import date, datetime
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_doctor
from app.models.doctor import Doctor
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardFilter,
    TimeRange,
    AppointmentStats,
    RevenueStats,
    PatientStats,
    TreatmentStats,
    ChatStats,
    DailySchedule,
    PerformanceMetric,
    Alert
)
from app.services.dashboard_service import (
    get_dashboard_overview,
    get_appointment_stats,
    get_revenue_stats,
    get_patient_stats,
    get_treatment_stats,
    get_chat_stats,
    get_daily_schedule,
    get_performance_metrics,
    get_alerts
)

router = APIRouter()

@router.get("/dashboard", response_model=DashboardResponse)
async def get_doctor_dashboard(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    service_types: Optional[List[str]] = Query(None),
    patient_groups: Optional[List[str]] = Query(None),
    conditions: Optional[List[str]] = Query(None),
    locations: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """
    الحصول على نظرة عامة كاملة على لوحة تحكم الطبيب
    
    يشمل:
    - إحصائيات المواعيد
    - إحصائيات الإيرادات
    - إحصائيات المرضى
    - إحصائيات العلاج
    - إحصائيات المحادثات
    - الجدول اليومي
    - مقاييس الأداء
    - التنبيهات
    
    يمكن تصفية النتائج باستخدام:
    - نطاق تاريخي (start_date, end_date)
    - أنواع الخدمات
    - مجموعات المرضى
    - الحالات المرضية
    - المواقع
    """
    filters = None
    if any([start_date, end_date, service_types, patient_groups, conditions, locations]):
        filters = DashboardFilter(
            time_range=TimeRange(
                start_date=start_date or date.today(),
                end_date=end_date or date.today()
            ) if start_date or end_date else None,
            service_types=service_types,
            patient_groups=patient_groups,
            conditions=conditions,
            locations=locations
        )
    
    return await get_dashboard_overview(db, current_doctor.id, filters)

@router.get("/dashboard/appointments", response_model=AppointmentStats)
async def get_doctor_appointment_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على إحصائيات المواعيد"""
    time_range = None
    if start_date and end_date:
        time_range = TimeRange(start_date=start_date, end_date=end_date)
    
    return await get_appointment_stats(db, current_doctor.id, time_range)

@router.get("/dashboard/revenue", response_model=RevenueStats)
async def get_doctor_revenue_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على إحصائيات الإيرادات"""
    time_range = None
    if start_date and end_date:
        time_range = TimeRange(start_date=start_date, end_date=end_date)
    
    return await get_revenue_stats(db, current_doctor.id, time_range)

@router.get("/dashboard/patients", response_model=PatientStats)
async def get_doctor_patient_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على إحصائيات المرضى"""
    time_range = None
    if start_date and end_date:
        time_range = TimeRange(start_date=start_date, end_date=end_date)
    
    return await get_patient_stats(db, current_doctor.id, time_range)

@router.get("/dashboard/treatments", response_model=TreatmentStats)
async def get_doctor_treatment_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على إحصائيات العلاج"""
    time_range = None
    if start_date and end_date:
        time_range = TimeRange(start_date=start_date, end_date=end_date)
    
    return await get_treatment_stats(db, current_doctor.id, time_range)

@router.get("/dashboard/chats", response_model=ChatStats)
async def get_doctor_chat_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على إحصائيات المحادثات"""
    time_range = None
    if start_date and end_date:
        time_range = TimeRange(start_date=start_date, end_date=end_date)
    
    return await get_chat_stats(db, current_doctor.id, time_range)

@router.get("/dashboard/schedule/{date}", response_model=DailySchedule)
async def get_doctor_daily_schedule(
    date: date,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على الجدول اليومي"""
    return await get_daily_schedule(db, current_doctor.id, date)

@router.get("/dashboard/performance", response_model=List[PerformanceMetric])
async def get_doctor_performance_metrics(
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على مقاييس الأداء"""
    return await get_performance_metrics(db, current_doctor.id)

@router.get("/dashboard/alerts", response_model=List[Alert])
async def get_doctor_alerts(
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """الحصول على التنبيهات"""
    return await get_alerts(db, current_doctor.id)

@router.post("/dashboard/alerts/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: str,
    db: Session = Depends(get_db),
    current_doctor: Doctor = Depends(get_current_doctor)
):
    """تحديد تنبيه كمقروء"""
    alerts = await get_alerts(db, current_doctor.id)
    alert = next((a for a in alerts if str(a.id) == alert_id), None)
    
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التنبيه غير موجود"
        )
    
    alert.is_read = True
    return {"status": "success"}
