"""
Doctor Dashboard Service
"""
from typing import List, Dict, Optional
from datetime import datetime, date, timedelta
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from fastapi import HTTPException, status

from app.models.doctor import Doctor
from app.models.appointment import Appointment
from app.models.chat import ChatSession
from app.models.user import User
from app.models.medication import Prescription
from app.schemas.dashboard import (
    AppointmentStats,
    RevenueStats,
    PatientStats,
    TreatmentStats,
    ChatStats,
    DailySchedule,
    DashboardOverview,
    TimeRange,
    DashboardFilter,
    PerformanceMetric,
    Alert,
    DashboardResponse
)

def get_appointment_stats(db: Session, doctor_id: UUID, time_range: Optional[TimeRange] = None) -> AppointmentStats:
    """حساب إحصائيات المواعيد"""
    query = db.query(Appointment).filter(Appointment.doctor_id == doctor_id)
    
    if time_range:
        query = query.filter(
            and_(
                Appointment.scheduled_at >= time_range.start_date,
                Appointment.scheduled_at <= time_range.end_date
            )
        )
    
    total = query.count()
    completed = query.filter(Appointment.status == "completed").count()
    cancelled = query.filter(Appointment.status == "cancelled").count()
    upcoming = query.filter(
        and_(
            Appointment.status == "scheduled",
            Appointment.scheduled_at > datetime.now()
        )
    ).count()
    
    completion_rate = (completed / total) * 100 if total > 0 else 0
    cancellation_rate = (cancelled / total) * 100 if total > 0 else 0
    
    # حساب متوسط مدة المواعيد
    completed_appointments = query.filter(Appointment.status == "completed").all()
    total_duration = sum((apt.end_time - apt.start_time).total_seconds() / 3600 
                        for apt in completed_appointments if apt.end_time)
    avg_duration = total_duration / len(completed_appointments) if completed_appointments else 0
    
    return AppointmentStats(
        total=total,
        completed=completed,
        cancelled=cancelled,
        upcoming=upcoming,
        completion_rate=completion_rate,
        cancellation_rate=cancellation_rate,
        avg_duration=avg_duration
    )

def get_revenue_stats(db: Session, doctor_id: UUID, time_range: Optional[TimeRange] = None) -> RevenueStats:
    """حساب إحصائيات الإيرادات"""
    query = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "completed",
            Appointment.payment_status == "paid"
        )
    )
    
    if time_range:
        query = query.filter(
            and_(
                Appointment.scheduled_at >= time_range.start_date,
                Appointment.scheduled_at <= time_range.end_date
            )
        )
    
    # حساب الإيرادات الإجمالية
    total_revenue = sum(apt.fee for apt in query.all())
    
    # حساب إيرادات الشهر الحالي
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_revenue = sum(
        apt.fee for apt in query.filter(Appointment.scheduled_at >= current_month_start).all()
    )
    
    # حساب إيرادات الشهر السابق
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    last_month_revenue = sum(
        apt.fee for apt in query.filter(
            and_(
                Appointment.scheduled_at >= last_month_start,
                Appointment.scheduled_at < current_month_start
            )
        ).all()
    )
    
    # حساب معدل النمو
    growth_rate = ((current_month_revenue - last_month_revenue) / last_month_revenue * 100 
                   if last_month_revenue > 0 else 0)
    
    # تصنيف الإيرادات حسب نوع الخدمة
    revenue_by_service = {}
    for apt in query.all():
        service_type = apt.consultation_type
        revenue_by_service[service_type] = revenue_by_service.get(service_type, 0) + apt.fee
    
    # تصنيف الإيرادات حسب الشهر
    revenue_by_month = {}
    for apt in query.all():
        month_key = apt.scheduled_at.strftime("%Y-%m")
        revenue_by_month[month_key] = revenue_by_month.get(month_key, 0) + apt.fee
    
    return RevenueStats(
        total_revenue=total_revenue,
        current_month=current_month_revenue,
        last_month=last_month_revenue,
        growth_rate=growth_rate,
        by_service=revenue_by_service,
        by_month=revenue_by_month
    )

def get_patient_stats(db: Session, doctor_id: UUID, time_range: Optional[TimeRange] = None) -> PatientStats:
    """حساب إحصائيات المرضى"""
    # الحصول على جميع المرضى
    patient_query = db.query(User).join(Appointment).filter(Appointment.doctor_id == doctor_id)
    
    if time_range:
        patient_query = patient_query.filter(
            and_(
                Appointment.scheduled_at >= time_range.start_date,
                Appointment.scheduled_at <= time_range.end_date
            )
        )
    
    total_patients = patient_query.distinct(User.id).count()
    
    # حساب المرضى الجدد
    new_patients = patient_query.filter(
        User.created_at >= (datetime.now() - timedelta(days=30))
    ).distinct(User.id).count()
    
    # حساب المرضى العائدين
    returning_patients = db.query(User).join(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "completed"
        )
    ).group_by(User.id).having(func.count(Appointment.id) > 1).count()
    
    # حساب معدل الاحتفاظ
    retention_rate = (returning_patients / total_patients * 100) if total_patients > 0 else 0
    
    # حساب متوسط التقييم ومعدل الرضا
    ratings = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.rating.isnot(None)
        )
    )
    avg_rating = ratings.with_entities(func.avg(Appointment.rating)).scalar() or 0
    satisfaction_rate = ratings.filter(Appointment.rating >= 4).count() / ratings.count() * 100 if ratings.count() > 0 else 0
    
    # حساب الديموغرافيا
    demographics = {}
    for user in patient_query.all():
        age_group = calculate_age_group(user.date_of_birth)
        demographics[age_group] = demographics.get(age_group, 0) + 1
    
    return PatientStats(
        total_patients=total_patients,
        new_patients=new_patients,
        returning_patients=returning_patients,
        retention_rate=retention_rate,
        satisfaction_rate=satisfaction_rate,
        avg_rating=avg_rating,
        demographics=demographics
    )

def get_treatment_stats(db: Session, doctor_id: UUID, time_range: Optional[TimeRange] = None) -> TreatmentStats:
    """حساب إحصائيات العلاج"""
    query = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "completed"
        )
    )
    
    if time_range:
        query = query.filter(
            and_(
                Appointment.scheduled_at >= time_range.start_date,
                Appointment.scheduled_at <= time_range.end_date
            )
        )
    
    total_treatments = query.count()
    
    # حساب معدل النجاح
    successful_treatments = query.filter(Appointment.treatment_outcome == "successful").count()
    success_rate = (successful_treatments / total_treatments * 100) if total_treatments > 0 else 0
    
    # حساب الحالات الشائعة
    common_conditions = {}
    for apt in query.all():
        for condition in apt.diagnosis or []:
            common_conditions[condition] = common_conditions.get(condition, 0) + 1
    
    # حساب متوسط وقت التعافي
    recovery_times = [apt.recovery_time.total_seconds() / (24 * 3600) for apt in query.all() if apt.recovery_time]
    avg_recovery_time = sum(recovery_times) / len(recovery_times) if recovery_times else 0
    
    # حساب فعالية الأدوية
    medication_effectiveness = {}
    prescriptions = db.query(Prescription).filter(Prescription.doctor_id == doctor_id)
    for prescription in prescriptions.all():
        if prescription.effectiveness_rating:
            medication_effectiveness[prescription.medication_name] = (
                medication_effectiveness.get(prescription.medication_name, 0) + 
                prescription.effectiveness_rating
            ) / 2
    
    return TreatmentStats(
        total_treatments=total_treatments,
        success_rate=success_rate,
        common_conditions=common_conditions,
        avg_recovery_time=avg_recovery_time,
        medication_effectiveness=medication_effectiveness
    )

def get_chat_stats(db: Session, doctor_id: UUID, time_range: Optional[TimeRange] = None) -> ChatStats:
    """حساب إحصائيات المحادثات"""
    query = db.query(ChatSession).filter(ChatSession.doctor_id == doctor_id)
    
    if time_range:
        query = query.filter(
            and_(
                ChatSession.created_at >= time_range.start_date,
                ChatSession.created_at <= time_range.end_date
            )
        )
    
    total_chats = query.count()
    
    # حساب متوسط وقت الاستجابة
    response_times = []
    for chat in query.all():
        messages = sorted(chat.messages, key=lambda x: x.timestamp)
        for i in range(1, len(messages)):
            if messages[i].sender_type == "doctor" and messages[i-1].sender_type == "patient":
                response_time = (messages[i].timestamp - messages[i-1].timestamp).total_seconds()
                response_times.append(response_time)
    
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # حساب معدل الرضا
    satisfaction_rate = (
        query.filter(ChatSession.satisfaction_rating >= 4).count() / 
        query.filter(ChatSession.satisfaction_rating.isnot(None)).count() * 100
    ) if query.filter(ChatSession.satisfaction_rating.isnot(None)).count() > 0 else 0
    
    # حساب المواضيع الشائعة
    common_topics = {}
    for chat in query.all():
        for topic in chat.topics or []:
            common_topics[topic] = common_topics.get(topic, 0) + 1
    
    # حساب معدل التصعيد
    escalated_chats = query.filter(ChatSession.was_escalated == True).count()
    escalation_rate = (escalated_chats / total_chats * 100) if total_chats > 0 else 0
    
    return ChatStats(
        total_chats=total_chats,
        avg_response_time=avg_response_time,
        satisfaction_rate=satisfaction_rate,
        common_topics=common_topics,
        escalation_rate=escalation_rate
    )

def get_daily_schedule(db: Session, doctor_id: UUID, date: date) -> DailySchedule:
    """الحصول على الجدول اليومي"""
    # الحصول على المواعيد
    appointments = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            func.date(Appointment.scheduled_at) == date
        )
    ).order_by(Appointment.scheduled_at).all()
    
    # تحويل المواعيد إلى قائمة
    appointments_list = [
        {
            "id": str(apt.id),
            "patient_name": f"{apt.patient.first_name} {apt.patient.last_name}",
            "time": apt.scheduled_at.strftime("%H:%M"),
            "duration": apt.duration,
            "type": apt.consultation_type,
            "status": apt.status
        }
        for apt in appointments
    ]
    
    # حساب الفترات المتاحة
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    working_hours = doctor.working_hours.get(date.strftime("%A").lower())
    
    available_slots = []
    if working_hours and not working_hours.is_closed:
        start_time = datetime.strptime(working_hours.start, "%H:%M").time()
        end_time = datetime.strptime(working_hours.end, "%H:%M").time()
        
        current_time = datetime.combine(date, start_time)
        end_datetime = datetime.combine(date, end_time)
        
        while current_time < end_datetime:
            slot_end = current_time + timedelta(minutes=doctor.consultation_duration)
            
            # التحقق من عدم تداخل الموعد مع المواعيد الموجودة
            is_available = True
            for apt in appointments:
                if (current_time >= apt.scheduled_at and current_time < apt.end_time) or \
                   (slot_end > apt.scheduled_at and slot_end <= apt.end_time):
                    is_available = False
                    break
            
            if is_available:
                available_slots.append({
                    "start_time": current_time.strftime("%H:%M"),
                    "end_time": slot_end.strftime("%H:%M")
                })
            
            current_time = slot_end
    
    # الحصول على فترات الراحة
    breaks = []
    if working_hours and working_hours.breaks:
        breaks = [
            {
                "start_time": break_time.start,
                "end_time": break_time.end
            }
            for break_time in working_hours.breaks
        ]
    
    # حساب إجمالي ساعات العمل
    total_hours = 0
    if working_hours and not working_hours.is_closed:
        start = datetime.strptime(working_hours.start, "%H:%M")
        end = datetime.strptime(working_hours.end, "%H:%M")
        total_hours = (end - start).total_seconds() / 3600
        
        # طرح وقت الاستراحات
        for break_time in breaks:
            break_start = datetime.strptime(break_time["start_time"], "%H:%M")
            break_end = datetime.strptime(break_time["end_time"], "%H:%M")
            total_hours -= (break_end - break_start).total_seconds() / 3600
    
    return DailySchedule(
        date=date,
        appointments=appointments_list,
        available_slots=available_slots,
        breaks=breaks,
        total_hours=total_hours
    )

def get_performance_metrics(db: Session, doctor_id: UUID) -> List[PerformanceMetric]:
    """الحصول على مقاييس الأداء"""
    metrics = []
    
    # متوسط التقييم
    current_rating = db.query(func.avg(Appointment.rating)).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.rating.isnot(None),
            Appointment.scheduled_at >= datetime.now() - timedelta(days=30)
        )
    ).scalar() or 0
    
    previous_rating = db.query(func.avg(Appointment.rating)).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.rating.isnot(None),
            Appointment.scheduled_at >= datetime.now() - timedelta(days=60),
            Appointment.scheduled_at < datetime.now() - timedelta(days=30)
        )
    ).scalar() or 0
    
    rating_change = ((current_rating - previous_rating) / previous_rating * 100) if previous_rating > 0 else 0
    
    metrics.append(
        PerformanceMetric(
            metric_name="متوسط التقييم",
            current_value=current_rating,
            previous_value=previous_rating,
            change_percentage=rating_change,
            trend=get_rating_trend(db, doctor_id),
            benchmark=4.5
        )
    )
    
    # معدل إكمال المواعيد
    current_completion = get_completion_rate(db, doctor_id, days=30)
    previous_completion = get_completion_rate(db, doctor_id, days=60, offset=30)
    completion_change = ((current_completion - previous_completion) / previous_completion * 100) if previous_completion > 0 else 0
    
    metrics.append(
        PerformanceMetric(
            metric_name="معدل إكمال المواعيد",
            current_value=current_completion,
            previous_value=previous_completion,
            change_percentage=completion_change,
            trend=get_completion_trend(db, doctor_id),
            benchmark=90
        )
    )
    
    return metrics

def get_alerts(db: Session, doctor_id: UUID) -> List[Alert]:
    """الحصول على التنبيهات"""
    alerts = []
    
    # تنبيهات المواعيد القادمة
    upcoming_appointments = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at > datetime.now(),
            Appointment.scheduled_at <= datetime.now() + timedelta(hours=24)
        )
    ).all()
    
    for apt in upcoming_appointments:
        alerts.append(
            Alert(
                id=UUID(int=len(alerts) + 1),
                type="appointment",
                message=f"لديك موعد قادم مع {apt.patient.first_name} {apt.patient.last_name} في {apt.scheduled_at.strftime('%H:%M')}",
                severity="info",
                created_at=datetime.now(),
                is_read=False,
                action_required=True,
                link=f"/appointments/{apt.id}"
            )
        )
    
    # تنبيهات التقييمات المنخفضة
    low_ratings = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.rating <= 3,
            Appointment.scheduled_at >= datetime.now() - timedelta(days=7)
        )
    ).all()
    
    for apt in low_ratings:
        alerts.append(
            Alert(
                id=UUID(int=len(alerts) + 1),
                type="rating",
                message=f"تقييم منخفض ({apt.rating}) من المريض {apt.patient.first_name} {apt.patient.last_name}",
                severity="warning",
                created_at=datetime.now(),
                is_read=False,
                action_required=True,
                link=f"/appointments/{apt.id}"
            )
        )
    
    # تنبيهات المحادثات غير المجاب عليها
    unanswered_chats = db.query(ChatSession).filter(
        and_(
            ChatSession.doctor_id == doctor_id,
            ChatSession.status == "pending",
            ChatSession.created_at >= datetime.now() - timedelta(hours=2)
        )
    ).all()
    
    for chat in unanswered_chats:
        alerts.append(
            Alert(
                id=UUID(int=len(alerts) + 1),
                type="chat",
                message=f"محادثة غير مجاب عليها من المريض {chat.patient.first_name} {chat.patient.last_name}",
                severity="warning",
                created_at=datetime.now(),
                is_read=False,
                action_required=True,
                link=f"/chats/{chat.id}"
            )
        )
    
    return sorted(alerts, key=lambda x: x.created_at, reverse=True)

def get_dashboard_overview(
    db: Session,
    doctor_id: UUID,
    filters: Optional[DashboardFilter] = None
) -> DashboardResponse:
    """الحصول على نظرة عامة على لوحة التحكم"""
    # التحقق من وجود الطبيب
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطبيب غير موجود"
        )
    
    # الحصول على الإحصائيات
    appointment_stats = get_appointment_stats(db, doctor_id, filters.time_range if filters else None)
    revenue_stats = get_revenue_stats(db, doctor_id, filters.time_range if filters else None)
    patient_stats = get_patient_stats(db, doctor_id, filters.time_range if filters else None)
    treatment_stats = get_treatment_stats(db, doctor_id, filters.time_range if filters else None)
    chat_stats = get_chat_stats(db, doctor_id, filters.time_range if filters else None)
    today_schedule = get_daily_schedule(db, doctor_id, date.today())
    
    # تجميع النظرة العامة
    overview = DashboardOverview(
        appointment_stats=appointment_stats,
        revenue_stats=revenue_stats,
        patient_stats=patient_stats,
        treatment_stats=treatment_stats,
        chat_stats=chat_stats,
        today_schedule=today_schedule
    )
    
    # الحصول على مقاييس الأداء والتنبيهات
    performance_metrics = get_performance_metrics(db, doctor_id)
    alerts = get_alerts(db, doctor_id)
    
    return DashboardResponse(
        overview=overview,
        performance_metrics=performance_metrics,
        alerts=alerts,
        last_updated=datetime.now()
    )

# Helper Functions

def calculate_age_group(birth_date: date) -> str:
    """حساب الفئة العمرية"""
    if not birth_date:
        return "غير محدد"
    
    age = (date.today() - birth_date).days // 365
    
    if age < 18:
        return "أقل من 18"
    elif age < 30:
        return "18-29"
    elif age < 45:
        return "30-44"
    elif age < 60:
        return "45-59"
    else:
        return "60 فأكثر"

def get_rating_trend(db: Session, doctor_id: UUID, months: int = 6) -> List[float]:
    """الحصول على اتجاه التقييمات"""
    trend = []
    for i in range(months - 1, -1, -1):
        start_date = datetime.now() - timedelta(days=(i + 1) * 30)
        end_date = datetime.now() - timedelta(days=i * 30)
        
        avg_rating = db.query(func.avg(Appointment.rating)).filter(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.rating.isnot(None),
                Appointment.scheduled_at >= start_date,
                Appointment.scheduled_at < end_date
            )
        ).scalar() or 0
        
        trend.append(float(avg_rating))
    
    return trend

def get_completion_rate(db: Session, doctor_id: UUID, days: int = 30, offset: int = 0) -> float:
    """حساب معدل إكمال المواعيد"""
    start_date = datetime.now() - timedelta(days=days + offset)
    end_date = datetime.now() - timedelta(days=offset)
    
    total = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at >= start_date,
            Appointment.scheduled_at < end_date
        )
    ).count()
    
    completed = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.status == "completed",
            Appointment.scheduled_at >= start_date,
            Appointment.scheduled_at < end_date
        )
    ).count()
    
    return (completed / total * 100) if total > 0 else 0

def get_completion_trend(db: Session, doctor_id: UUID, months: int = 6) -> List[float]:
    """الحصول على اتجاه معدل إكمال المواعيد"""
    trend = []
    for i in range(months - 1, -1, -1):
        completion_rate = get_completion_rate(db, doctor_id, days=30, offset=i * 30)
        trend.append(completion_rate)
    
    return trend 