"""
Appointment System Service
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta, time
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, between
from fastapi import HTTPException, status

from app.models.appointment import (
    Appointment,
    AppointmentFeedback,
    DoctorSchedule,
    AppointmentReminder,
    AppointmentNotification
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentStatus,
    PaymentStatus,
    AppointmentSearchParams,
    AppointmentStats,
    DoctorAvailability,
    AppointmentConflictCheck,
    TimeSlot
)
from app.services.notification_service import send_notification
from app.services.payment_service import process_payment, refund_payment

def create_appointment(
    db: Session,
    appointment: AppointmentCreate,
    check_availability: bool = True
) -> Appointment:
    """إنشاء موعد جديد"""
    # التحقق من توفر الموعد
    if check_availability:
        if not is_slot_available(db, appointment.doctor_id, appointment.scheduled_at, appointment.duration_minutes):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="الموعد المطلوب غير متاح"
            )
    
    # إنشاء الموعد
    db_appointment = Appointment(
        doctor_id=appointment.doctor_id,
        patient_id=appointment.patient_id,
        appointment_type=appointment.appointment_type,
        scheduled_at=appointment.scheduled_at,
        duration_minutes=appointment.duration_minutes,
        reason=appointment.reason,
        notes=appointment.notes,
        virtual_meeting_link=appointment.virtual_meeting_link,
        symptoms=appointment.symptoms,
        medical_history_required=appointment.medical_history_required,
        insurance_required=appointment.insurance_required,
        fee=appointment.fee
    )
    
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # إنشاء التذكيرات
    create_appointment_reminders(db, db_appointment)
    
    # إرسال الإشعارات
    notify_appointment_creation(db, db_appointment)
    
    return db_appointment

def update_appointment(
    db: Session,
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    check_availability: bool = True
) -> Appointment:
    """تحديث موعد"""
    appointment = get_appointment(db, appointment_id)
    
    # التحقق من إمكانية التحديث
    if appointment.status in [AppointmentStatus.COMPLETED, AppointmentStatus.CANCELLED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكن تحديث موعد مكتمل أو ملغي"
        )
    
    # التحقق من توفر الموعد الجديد
    if update_data.scheduled_at and check_availability:
        if not is_slot_available(
            db,
            appointment.doctor_id,
            update_data.scheduled_at,
            update_data.duration_minutes or appointment.duration_minutes,
            exclude_appointment_id=appointment_id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="الموعد المطلوب غير متاح"
            )
    
    # تحديث البيانات
    for field, value in update_data.dict(exclude_unset=True).items():
        setattr(appointment, field, value)
    
    # معالجة تغيير الحالة
    if update_data.status:
        handle_status_change(db, appointment, update_data.status)
    
    db.commit()
    db.refresh(appointment)
    
    # إرسال الإشعارات
    notify_appointment_update(db, appointment)
    
    return appointment

def cancel_appointment(
    db: Session,
    appointment_id: UUID,
    cancellation_reason: str,
    cancelled_by_doctor: bool = False
) -> Appointment:
    """إلغاء موعد"""
    appointment = get_appointment(db, appointment_id)
    
    # التحقق من إمكانية الإلغاء
    if appointment.status != AppointmentStatus.CONFIRMED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لا يمكن إلغاء موعد غير مؤكد"
        )
    
    # حساب وقت الإلغاء
    cancellation_time = datetime.utcnow()
    hours_until_appointment = (appointment.scheduled_at - cancellation_time).total_seconds() / 3600
    
    # التحقق من سياسة الإلغاء
    if not cancelled_by_doctor and hours_until_appointment < 24:
        # تطبيق رسوم الإلغاء المتأخر
        apply_late_cancellation_fee(db, appointment)
    
    # تحديث الموعد
    appointment.status = AppointmentStatus.CANCELLED
    appointment.cancelled_at = cancellation_time
    appointment.cancellation_reason = cancellation_reason
    
    # إلغاء التذكيرات المجدولة
    cancel_appointment_reminders(db, appointment)
    
    # استرجاع المدفوعات إذا كان ذلك مناسباً
    if appointment.payment_status == PaymentStatus.PAID:
        process_refund(db, appointment)
    
    db.commit()
    db.refresh(appointment)
    
    # إرسال الإشعارات
    notify_appointment_cancellation(db, appointment)
    
    return appointment

def get_doctor_availability(
    db: Session,
    doctor_id: UUID,
    start_date: datetime,
    end_date: datetime
) -> DoctorAvailability:
    """الحصول على توفر الطبيب"""
    # الحصول على جدول الطبيب
    schedules = db.query(DoctorSchedule).filter(
        and_(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.date.between(start_date, end_date),
            DoctorSchedule.is_available == True
        )
    ).all()
    
    # الحصول على المواعيد الحالية
    appointments = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.scheduled_at.between(start_date, end_date),
            Appointment.status.in_([
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.PENDING
            ])
        )
    ).all()
    
    # تحليل الفترات المتاحة
    available_slots = analyze_available_slots(schedules, appointments)
    
    return DoctorAvailability(
        doctor_id=doctor_id,
        available_dates=[s.date for s in schedules],
        available_slots=available_slots,
        next_available_slot=find_next_available_slot(available_slots),
        regular_schedule=get_regular_schedule(db, doctor_id),
        vacation_dates=get_vacation_dates(db, doctor_id),
        max_daily_appointments=get_max_daily_appointments(db, doctor_id),
        appointment_buffer_minutes=15
    )

def get_appointment_stats(
    db: Session,
    doctor_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> AppointmentStats:
    """الحصول على إحصائيات المواعيد"""
    query = db.query(Appointment)
    
    if doctor_id:
        query = query.filter(Appointment.doctor_id == doctor_id)
    if patient_id:
        query = query.filter(Appointment.patient_id == patient_id)
    if start_date:
        query = query.filter(Appointment.scheduled_at >= start_date)
    if end_date:
        query = query.filter(Appointment.scheduled_at <= end_date)
    
    appointments = query.all()
    
    if not appointments:
        return AppointmentStats(
            total_appointments=0,
            completed_appointments=0,
            cancelled_appointments=0,
            no_show_appointments=0,
            average_duration=0,
            total_revenue=0,
            most_common_type=None,
            busiest_day="",
            average_rating=0,
            patient_satisfaction=0
        )
    
    # حساب الإحصائيات الأساسية
    total = len(appointments)
    completed = sum(1 for a in appointments if a.status == AppointmentStatus.COMPLETED)
    cancelled = sum(1 for a in appointments if a.status == AppointmentStatus.CANCELLED)
    no_show = sum(1 for a in appointments if a.status == AppointmentStatus.NO_SHOW)
    
    # حساب متوسط المدة
    avg_duration = sum(a.duration_minutes for a in appointments) / total
    
    # حساب الإيرادات
    total_revenue = sum(a.fee for a in appointments if a.payment_status == PaymentStatus.PAID)
    
    # تحليل النوع الأكثر شيوعاً
    type_counts = {}
    for a in appointments:
        type_counts[a.appointment_type] = type_counts.get(a.appointment_type, 0) + 1
    most_common_type = max(type_counts.items(), key=lambda x: x[1])[0]
    
    # تحليل اليوم الأكثر ازدحاماً
    day_counts = {}
    for a in appointments:
        day = a.scheduled_at.strftime("%A")
        day_counts[day] = day_counts.get(day, 0) + 1
    busiest_day = max(day_counts.items(), key=lambda x: x[1])[0]
    
    # حساب متوسط التقييم ورضا المرضى
    feedbacks = db.query(AppointmentFeedback).filter(
        AppointmentFeedback.appointment_id.in_([a.id for a in appointments])
    ).all()
    
    avg_rating = 0
    patient_satisfaction = 0
    
    if feedbacks:
        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
        patient_satisfaction = sum(1 for f in feedbacks if f.would_recommend) / len(feedbacks) * 100
    
    return AppointmentStats(
        total_appointments=total,
        completed_appointments=completed,
        cancelled_appointments=cancelled,
        no_show_appointments=no_show,
        average_duration=avg_duration,
        total_revenue=total_revenue,
        most_common_type=most_common_type,
        busiest_day=busiest_day,
        average_rating=avg_rating,
        patient_satisfaction=patient_satisfaction
    )

def search_appointments(
    db: Session,
    params: AppointmentSearchParams
) -> List[Appointment]:
    """البحث عن المواعيد"""
    query = db.query(Appointment)
    
    if params.doctor_id:
        query = query.filter(Appointment.doctor_id == params.doctor_id)
    if params.patient_id:
        query = query.filter(Appointment.patient_id == params.patient_id)
    if params.status:
        query = query.filter(Appointment.status.in_(params.status))
    if params.appointment_type:
        query = query.filter(Appointment.appointment_type.in_(params.appointment_type))
    if params.start_date:
        query = query.filter(Appointment.scheduled_at >= params.start_date)
    if params.end_date:
        query = query.filter(Appointment.scheduled_at <= params.end_date)
    if params.payment_status:
        query = query.filter(Appointment.payment_status.in_(params.payment_status))
    
    return query.order_by(Appointment.scheduled_at).all()

# Helper Functions

def is_slot_available(
    db: Session,
    doctor_id: UUID,
    scheduled_at: datetime,
    duration_minutes: int,
    exclude_appointment_id: Optional[UUID] = None
) -> bool:
    """التحقق من توفر الموعد"""
    # التحقق من جدول الطبيب
    schedule = db.query(DoctorSchedule).filter(
        and_(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.date == scheduled_at.date(),
            DoctorSchedule.is_available == True
        )
    ).first()
    
    if not schedule:
        return False
    
    # التحقق من الفترة المطلوبة
    slot_end = scheduled_at + timedelta(minutes=duration_minutes)
    
    # التحقق من تعارض المواعيد
    query = db.query(Appointment).filter(
        and_(
            Appointment.doctor_id == doctor_id,
            Appointment.status.in_([AppointmentStatus.CONFIRMED, AppointmentStatus.PENDING]),
            or_(
                and_(
                    Appointment.scheduled_at <= scheduled_at,
                    Appointment.scheduled_at + timedelta(minutes=Appointment.duration_minutes) > scheduled_at
                ),
                and_(
                    Appointment.scheduled_at < slot_end,
                    Appointment.scheduled_at + timedelta(minutes=Appointment.duration_minutes) >= slot_end
                )
            )
        )
    )
    
    if exclude_appointment_id:
        query = query.filter(Appointment.id != exclude_appointment_id)
    
    conflicting_appointments = query.count()
    
    return conflicting_appointments == 0

def create_appointment_reminders(db: Session, appointment: Appointment) -> None:
    """إنشاء تذكيرات الموعد"""
    reminders = [
        # تذكير قبل يوم
        AppointmentReminder(
            appointment_id=appointment.id,
            recipient_id=appointment.patient_id,
            reminder_type="email",
            scheduled_time=appointment.scheduled_at - timedelta(days=1),
            message=f"تذكير: لديك موعد غداً في {appointment.scheduled_at.strftime('%H:%M')}"
        ),
        # تذكير قبل ساعتين
        AppointmentReminder(
            appointment_id=appointment.id,
            recipient_id=appointment.patient_id,
            reminder_type="sms",
            scheduled_time=appointment.scheduled_at - timedelta(hours=2),
            message=f"تذكير: لديك موعد بعد ساعتين في {appointment.scheduled_at.strftime('%H:%M')}"
        )
    ]
    
    db.add_all(reminders)
    db.commit()

def notify_appointment_creation(db: Session, appointment: Appointment) -> None:
    """إرسال إشعارات إنشاء الموعد"""
    notifications = [
        # إشعار للمريض
        AppointmentNotification(
            appointment_id=appointment.id,
            notification_type="email",
            recipient_id=appointment.patient_id,
            message="تم إنشاء موعدك بنجاح",
            metadata={
                "appointment_details": {
                    "date": appointment.scheduled_at.strftime("%Y-%m-%d"),
                    "time": appointment.scheduled_at.strftime("%H:%M"),
                    "doctor_id": str(appointment.doctor_id)
                }
            }
        ),
        # إشعار للطبيب
        AppointmentNotification(
            appointment_id=appointment.id,
            notification_type="system",
            recipient_id=appointment.doctor_id,
            message="تم حجز موعد جديد",
            metadata={
                "appointment_details": {
                    "date": appointment.scheduled_at.strftime("%Y-%m-%d"),
                    "time": appointment.scheduled_at.strftime("%H:%M"),
                    "patient_id": str(appointment.patient_id)
                }
            }
        )
    ]
    
    db.add_all(notifications)
    db.commit()

def handle_status_change(
    db: Session,
    appointment: Appointment,
    new_status: AppointmentStatus
) -> None:
    """معالجة تغيير حالة الموعد"""
    old_status = appointment.status
    
    if new_status == AppointmentStatus.CONFIRMED and old_status == AppointmentStatus.PENDING:
        # إنشاء تذكيرات الموعد
        create_appointment_reminders(db, appointment)
        
    elif new_status == AppointmentStatus.COMPLETED:
        # إنشاء طلب تقييم
        create_feedback_request(db, appointment)
        
    elif new_status == AppointmentStatus.CANCELLED:
        # إلغاء التذكيرات
        cancel_appointment_reminders(db, appointment)
        
        # معالجة المدفوعات
        if appointment.payment_status == PaymentStatus.PAID:
            process_refund(db, appointment)

def analyze_available_slots(
    schedules: List[DoctorSchedule],
    appointments: List[Appointment]
) -> Dict[str, List[TimeSlot]]:
    """تحليل الفترات المتاحة"""
    available_slots = {}
    
    for schedule in schedules:
        date_str = schedule.date.strftime("%Y-%m-%d")
        day_slots = []
        
        # تحويل فترات الجدول إلى قائمة من الفترات المتاحة
        for slot in schedule.time_slots:
            start = datetime.combine(schedule.date, slot["start_time"])
            end = datetime.combine(schedule.date, slot["end_time"])
            
            # التحقق من تعارض المواعيد
            is_available = True
            for appointment in appointments:
                if (
                    appointment.scheduled_at >= start and
                    appointment.scheduled_at < end
                ):
                    is_available = False
                    break
            
            if is_available:
                day_slots.append(
                    TimeSlot(
                        start_time=slot["start_time"],
                        end_time=slot["end_time"],
                        is_available=True
                    )
                )
        
        available_slots[date_str] = day_slots
    
    return available_slots

def get_regular_schedule(db: Session, doctor_id: UUID) -> Dict[str, List[TimeSlot]]:
    """الحصول على الجدول المنتظم للطبيب"""
    schedules = db.query(DoctorSchedule).filter(
        and_(
            DoctorSchedule.doctor_id == doctor_id,
            DoctorSchedule.is_available == True
        )
    ).all()
    
    regular_schedule = {}
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    for day in days:
        day_schedules = [s for s in schedules if s.date.strftime("%A") == day]
        if day_schedules:
            # استخدام الجدول الأكثر تكراراً
            most_common_schedule = max(day_schedules, key=lambda x: len(x.time_slots))
            regular_schedule[day] = [
                TimeSlot(
                    start_time=slot["start_time"],
                    end_time=slot["end_time"],
                    is_available=True
                )
                for slot in most_common_schedule.time_slots
            ]
        else:
            regular_schedule[day] = []
    
    return regular_schedule
