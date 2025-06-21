"""
Follow-Up System API Endpoints
"""
from typing import List, Optional
from datetime import datetime
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.follow_up import (
    InteractionCreate,
    InteractionUpdate,
    InteractionInDB,
    Timeline,
    AnalyticsFilter,
    AnalyticsSummary,
    PatientSummary,
    DoctorSummary
)
from app.services.follow_up_service import (
    create_interaction,
    update_interaction,
    get_patient_timeline,
    get_analytics_summary,
    get_patient_summary,
    get_doctor_summary
)

router = APIRouter(prefix="/follow-up", tags=["follow-up"])

@router.post("/interactions/", response_model=InteractionInDB)
async def create_new_interaction(
    interaction: InteractionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """إنشاء تفاعل جديد"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if interaction.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بإنشاء تفاعلات لمرضى آخرين"
            )
    
    return create_interaction(db, interaction)

@router.put("/interactions/{interaction_id}", response_model=InteractionInDB)
async def update_existing_interaction(
    interaction_id: UUID,
    update_data: InteractionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """تحديث تفاعل موجود"""
    # التحقق من وجود التفاعل وصلاحيات المستخدم
    interaction = db.query(InteractionInDB).filter(InteractionInDB.id == interaction_id).first()
    if not interaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التفاعل غير موجود"
        )
    
    if current_user.role not in ["doctor", "admin"]:
        if interaction.patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بتحديث هذا التفاعل"
            )
    
    return update_interaction(db, interaction_id, update_data)

@router.get("/timeline/patient/{patient_id}", response_model=Timeline)
async def get_patient_interaction_timeline(
    patient_id: UUID,
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    interaction_types: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على الجدول الزمني للمريض"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض تفاعلات مرضى آخرين"
            )
    
    return get_patient_timeline(
        db,
        patient_id,
        start_date,
        end_date,
        interaction_types
    )

@router.post("/analytics/", response_model=AnalyticsSummary)
async def get_interaction_analytics(
    filters: AnalyticsFilter,
    patient_id: Optional[UUID] = Query(None),
    doctor_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على تحليلات التفاعلات"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if patient_id and patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض تحليلات مرضى آخرين"
            )
        if doctor_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض تحليلات الأطباء"
            )
    
    return get_analytics_summary(db, patient_id, doctor_id, filters)

@router.get("/summary/patient/{patient_id}", response_model=PatientSummary)
async def get_patient_interaction_summary(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على ملخص المريض"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        if patient_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="غير مصرح لك بعرض ملخص مرضى آخرين"
            )
    
    return get_patient_summary(db, patient_id)

@router.get("/summary/doctor/{doctor_id}", response_model=DoctorSummary)
async def get_doctor_interaction_summary(
    doctor_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """الحصول على ملخص الطبيب"""
    # التحقق من الصلاحيات
    if current_user.role not in ["doctor", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بعرض ملخص الأطباء"
        )
    
    if current_user.role == "doctor" and doctor_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="غير مصرح لك بعرض ملخص أطباء آخرين"
        )
    
    return get_doctor_summary(db, doctor_id) 