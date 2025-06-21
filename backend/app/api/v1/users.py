"""
User management API endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user, get_current_active_user
from app.core.security import has_permission
from app.models.user import User, UserRole
from app.schemas.user import (
    UserResponse,
    UserUpdate,
    PatientCreate,
    PatientResponse,
    PatientUpdate,
    DoctorCreate,
    DoctorResponse,
    DoctorUpdate
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
) -> UserResponse:
    """الحصول على معلومات المستخدم الحالي"""
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """تحديث معلومات المستخدم الحالي"""
    user_service = UserService(db)
    return await user_service.update_user(current_user.id, user_data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """الحصول على معلومات مستخدم محدد"""
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية للوصول إلى هذا المستخدم"
        )
    
    user_service = UserService(db)
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستخدم غير موجود"
        )
    return user

@router.get("/", response_model=List[UserResponse])
@has_permission([UserRole.ADMIN])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[UserResponse]:
    """الحصول على قائمة المستخدمين"""
    user_service = UserService(db)
    return await user_service.list_users(skip=skip, limit=limit, role=role, search=search)

@router.post("/patients", response_model=PatientResponse)
async def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db)
) -> PatientResponse:
    """إنشاء مريض جديد"""
    user_service = UserService(db)
    return await user_service.create_patient(patient_data)

@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PatientResponse:
    """الحصول على معلومات مريض محدد"""
    if not current_user.is_admin and not current_user.is_doctor and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية للوصول إلى هذا المريض"
        )
    
    user_service = UserService(db)
    patient = await user_service.get_patient_by_id(patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المريض غير موجود"
        )
    return patient

@router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PatientResponse:
    """تحديث معلومات مريض"""
    if not current_user.is_admin and current_user.id != patient_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية لتحديث هذا المريض"
        )
    
    user_service = UserService(db)
    return await user_service.update_patient(patient_id, patient_data)

@router.get("/patients", response_model=List[PatientResponse])
@has_permission([UserRole.ADMIN, UserRole.DOCTOR])
async def list_patients(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[PatientResponse]:
    """الحصول على قائمة المرضى"""
    user_service = UserService(db)
    return await user_service.list_patients(skip=skip, limit=limit, search=search)

@router.post("/doctors", response_model=DoctorResponse)
async def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db)
) -> DoctorResponse:
    """إنشاء طبيب جديد"""
    user_service = UserService(db)
    return await user_service.create_doctor(doctor_data)

@router.get("/doctors/{doctor_id}", response_model=DoctorResponse)
async def get_doctor(
    doctor_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DoctorResponse:
    """الحصول على معلومات طبيب محدد"""
    user_service = UserService(db)
    doctor = await user_service.get_doctor_by_id(doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطبيب غير موجود"
        )
    return doctor

@router.put("/doctors/{doctor_id}", response_model=DoctorResponse)
async def update_doctor(
    doctor_id: UUID,
    doctor_data: DoctorUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> DoctorResponse:
    """تحديث معلومات طبيب"""
    if not current_user.is_admin and current_user.id != doctor_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ليس لديك صلاحية لتحديث هذا الطبيب"
        )
    
    user_service = UserService(db)
    return await user_service.update_doctor(doctor_id, doctor_data)

@router.get("/doctors", response_model=List[DoctorResponse])
async def list_doctors(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    specialization: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[DoctorResponse]:
    """الحصول على قائمة الأطباء"""
    user_service = UserService(db)
    return await user_service.list_doctors(
        skip=skip,
        limit=limit,
        specialization=specialization,
        search=search
    )

@router.delete("/{user_id}")
@has_permission([UserRole.ADMIN])
async def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db)
) -> dict:
    """حذف مستخدم"""
    user_service = UserService(db)
    await user_service.delete_user(user_id)
    return {"message": "تم حذف المستخدم بنجاح"}
