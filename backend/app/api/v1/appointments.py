"""
Appointment System API Endpoints
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentInDB,
    AppointmentStatus,
    AppointmentSearchParams,
    AppointmentStats,
    DoctorAvailability,
    AppointmentFeedback
)
from app.services.appointment_service import (
    create_appointment,
    update_appointment,
    cancel_appointment,
    get_doctor_availability,
    get_appointment_stats,
    search_appointments
)

router = APIRouter(prefix="/appointments", tags=["appointments"])

@router.post("/", response_model=AppointmentInDB)
async def create_new_appointment(
    appointment: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """إنشاء موعد جديد"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if appointment.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بحجز مواعيد لمرضى آخرين"
            )
    
    return create_appointment(db, appointment)

@router.put("/{appointment_id}", response_model=AppointmentInDB)
async def update_existing_appointment(
    appointment_id: UUID,
    update_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث موعد موجود"""
    # التحقق من الصلاحيات
    appointment = db.query(AppointmentInDB).filter(AppointmentInDB.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الموعد غير موجود"
        )
    
    if current_user.role not in ["doctor", "admin"]:
        if appointment.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بتحديث هذا الموعد"
            )
    
    return update_appointment(db, appointment_id, update_data)

@router.delete("/{appointment_id}", response_model=AppointmentInDB)
async def cancel_existing_appointment(
    appointment_id: UUID,
    cancellation_reason: str = Query(..., min_length=10, max_length=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """إلغاء موعد"""
    # التحقق من الصلاحيات
    appointment = db.query(AppointmentInDB).filter(AppointmentInDB.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الموعد غير موجود"
        )
    
    is_doctor = current_user.role == "doctor" and appointment.doctor_id == current_user.id
    is_patient = appointment.patient_id == current_user.id
    is_admin = current_user.role == "admin"
    
    if not (is_doctor or is_patient or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بإلغاء هذا الموعد"
        )
    
    return cancel_appointment(
        db,
        appointment_id,
        cancellation_reason,
        cancelled_by_doctor=is_doctor
    )

@router.get("/availability/{doctor_id}", response_model=DoctorAvailability)
async def get_doctor_available_slots(
    doctor_id: UUID,
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على الفترات المتاحة للطبيب"""
    return get_doctor_availability(db, doctor_id, start_date, end_date)

@router.get("/stats", response_model=AppointmentStats)
async def get_appointments_statistics(
    doctor_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على إحصائيات المواعيد"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if patient_id and patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض إحصائيات مرضى آخرين"
            )
        if doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض إحصائيات الأطباء"
            )
    
    return get_appointment_stats(db, doctor_id, patient_id, start_date, end_date)

@router.post("/search", response_model=List[AppointmentInDB])
async def search_appointments_list(
    params: AppointmentSearchParams,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """البحث عن المواعيد"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        # المرضى يمكنهم فقط البحث عن مواعيدهم
        params.patient_id = current_user.id
    elif current_user.role == "doctor":
        # الأطباء يمكنهم فقط البحث عن مواعيدهم
        params.doctor_id = current_user.id
    
    return search_appointments(db, params)

@router.post("/{appointment_id}/feedback", response_model=AppointmentFeedback)
async def submit_appointment_feedback(
    appointment_id: UUID,
    feedback: AppointmentFeedback,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تقديم تقييم للموعد"""
    # التحقق من الصلاحيات
    appointment = db.query(AppointmentInDB).filter(AppointmentInDB.id == appointment_id).first()
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الموعد غير موجود"
        )
    
    if appointment.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بتقديم تقييم لهذا الموعد"
        )
    
    if appointment.status != AppointmentStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="يمكن تقديم التقييم فقط للمواعيد المكتملة"
        )
    
    if appointment.feedback_submitted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="تم تقديم تقييم لهذا الموعد مسبقاً"
        )
    
    # حفظ التقييم
    db_feedback = AppointmentFeedback(
        appointment_id=appointment_id,
        **feedback.dict(exclude={"appointment_id"})
    )
    
    db.add(db_feedback)
    
    # تحديث حالة التقييم في الموعد
    appointment.feedback_submitted = True
    
    db.commit()
    db.refresh(db_feedback)
    
    return db_feedback
