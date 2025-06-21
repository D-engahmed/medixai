"""
Doctor and Hospital Search API Endpoints
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.schemas.doctor import (
    DoctorPublic,
    DoctorDetail,
    HospitalPublic,
    DoctorSearchParams,
    HospitalSearchParams,
    GeoLocation,
    ReviewCreate,
    ReviewUpdate,
    ReviewInDB,
    DistanceUnit
)
from app.services.geo_service import search_doctors, search_hospitals
from app.services.doctor_service import (
    get_doctor_by_id,
    get_hospital_by_id,
    create_doctor_review,
    update_doctor_review,
    get_doctor_reviews
)
from app.models.doctor import ConsultationType, DoctorType
from app.models.user import User

router = APIRouter()

@router.get("/doctors/search", response_model=List[DoctorPublic])
async def search_doctors_endpoint(
    query: Optional[str] = None,
    specialization: Optional[str] = None,
    city: Optional[str] = None,
    consultation_type: Optional[ConsultationType] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_price: Optional[float] = Query(None, gt=0),
    insurance_provider: Optional[str] = None,
    language: Optional[str] = None,
    gender: Optional[str] = None,
    available_today: Optional[bool] = None,
    latitude: Optional[float] = Query(None, ge=-90, le=90, description="خط العرض"),
    longitude: Optional[float] = Query(None, ge=-180, le=180, description="خط الطول"),
    radius: Optional[float] = Query(10.0, gt=0, description="نصف قطر البحث"),
    distance_unit: DistanceUnit = Query(DistanceUnit.KM, description="وحدة قياس المسافة (كم/ميل)"),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    البحث عن الأطباء باستخدام معايير متعددة
    
    المعايير المدعومة:
    - البحث النصي (الاسم، التخصص، السيرة الذاتية)
    - التخصص
    - المدينة
    - نوع الاستشارة (حضوري، فيديو، دردشة)
    - الحد الأدنى للتقييم
    - الحد الأقصى للسعر
    - شركة التأمين
    - اللغة
    - الجنس
    - متاح اليوم
    - الموقع الجغرافي:
        - خط العرض (latitude)
        - خط الطول (longitude)
        - نصف قطر البحث (radius) - الافتراضي: 10
        - وحدة المسافة (distance_unit) - كم أو ميل
    """
    # تجميع معايير البحث
    search_params = DoctorSearchParams(
        query=query,
        specialization=specialization,
        city=city,
        consultation_type=consultation_type,
        min_rating=min_rating,
        max_price=max_price,
        insurance_provider=insurance_provider,
        language=language,
        gender=gender,
        available_today=available_today,
        location=GeoLocation(latitude=latitude, longitude=longitude) if latitude and longitude else None,
        radius_km=radius,
        distance_unit=distance_unit
    )
    
    # تنفيذ البحث
    doctors, total = search_doctors(db, search_params, limit, offset)
    
    # إضافة معلومات الصفحات في الرأس
    return {
        "items": doctors,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/doctors/{doctor_id}", response_model=DoctorDetail)
async def get_doctor_details(
    doctor_id: str,
    db: Session = Depends(get_db)
):
    """
    الحصول على التفاصيل الكاملة لطبيب محدد
    """
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطبيب غير موجود"
        )
    return doctor

@router.get("/hospitals/search", response_model=List[HospitalPublic])
async def search_hospitals_endpoint(
    query: Optional[str] = None,
    type: Optional[str] = None,
    city: Optional[str] = None,
    specialty: Optional[str] = None,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    insurance_provider: Optional[str] = None,
    has_emergency: Optional[bool] = None,
    latitude: Optional[float] = Query(None, ge=-90, le=90),
    longitude: Optional[float] = Query(None, ge=-180, le=180),
    radius_km: Optional[float] = Query(None, gt=0),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    البحث عن المستشفيات باستخدام معايير متعددة
    
    المعايير المدعومة:
    - البحث النصي (الاسم، الأقسام، التخصصات)
    - النوع (حكومي، خاص، تعليمي)
    - المدينة
    - التخصص
    - الحد الأدنى للتقييم
    - شركة التأمين
    - توفر قسم الطوارئ
    - الموقع الجغرافي (خط الطول، خط العرض، نصف قطر البحث)
    """
    # تجميع معايير البحث
    search_params = HospitalSearchParams(
        query=query,
        type=type,
        city=city,
        specialty=specialty,
        min_rating=min_rating,
        insurance_provider=insurance_provider,
        has_emergency=has_emergency,
        location=GeoLocation(latitude=latitude, longitude=longitude) if latitude and longitude else None,
        radius_km=radius_km
    )
    
    # تنفيذ البحث
    hospitals, total = search_hospitals(db, search_params, limit, offset)
    
    # إضافة معلومات الصفحات في الرأس
    return {
        "items": hospitals,
        "total": total,
        "limit": limit,
        "offset": offset
    }

@router.get("/hospitals/{hospital_id}", response_model=HospitalPublic)
async def get_hospital_details(
    hospital_id: str,
    db: Session = Depends(get_db)
):
    """
    الحصول على التفاصيل الكاملة لمستشفى محدد
    """
    hospital = get_hospital_by_id(db, hospital_id)
    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="المستشفى غير موجود"
        )
    return hospital

@router.post("/doctors/{doctor_id}/reviews", response_model=ReviewInDB)
async def create_review(
    doctor_id: str,
    review: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    إنشاء تقييم جديد لطبيب
    """
    # التحقق من وجود الطبيب
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطبيب غير موجود"
        )
    
    # التحقق من أن المستخدم لم يقم بتقييم هذا الطبيب من قبل
    existing_review = get_doctor_reviews(db, doctor_id, current_user.id)
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="لقد قمت بتقييم هذا الطبيب من قبل"
        )
    
    return create_doctor_review(db, review, current_user.id)

@router.put("/doctors/{doctor_id}/reviews/{review_id}", response_model=ReviewInDB)
async def update_review(
    doctor_id: str,
    review_id: str,
    review_update: ReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    تحديث تقييم موجود
    """
    # التحقق من وجود التقييم وملكيته
    existing_review = get_doctor_reviews(db, doctor_id, current_user.id, review_id)
    if not existing_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="التقييم غير موجود"
        )
    
    if existing_review.patient_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="لا يمكنك تعديل تقييم شخص آخر"
        )
    
    return update_doctor_review(db, review_id, review_update)

@router.get("/doctors/{doctor_id}/reviews", response_model=List[ReviewInDB])
async def get_doctor_reviews_endpoint(
    doctor_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """
    الحصول على تقييمات طبيب محدد
    """
    doctor = get_doctor_by_id(db, doctor_id)
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="الطبيب غير موجود"
        )
    
    reviews = get_doctor_reviews(db, doctor_id, limit=limit, offset=offset)
    return reviews
