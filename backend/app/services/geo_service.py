"""
Geo-Search Service for Doctors and Hospitals
"""
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from sqlalchemy.sql.expression import cast
from geoalchemy2 import Geography
from math import radians, sin, cos, sqrt, atan2

from app.models.doctor import Doctor, DoctorClinic, Hospital
from app.schemas.doctor import (
    DoctorSearchParams,
    HospitalSearchParams,
    GeoLocation,
    DoctorDistance,
    DistanceUnit
)

KM_TO_MILES = 0.621371

def format_distance(distance_km: float, unit: DistanceUnit) -> DoctorDistance:
    """
    تنسيق المسافة حسب الوحدة المطلوبة
    """
    if unit == DistanceUnit.MILES:
        value = distance_km * KM_TO_MILES
        text = f"{value:.1f} ميل"
    else:
        value = distance_km
        text = f"{value:.1f} كم"
    
    return DoctorDistance(
        value=value,
        unit=unit,
        text=text
    )

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    حساب المسافة بين نقطتين على سطح الأرض باستخدام صيغة هافرسين
    المسافة بالكيلومترات
    """
    R = 6371  # نصف قطر الأرض بالكيلومترات

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance

def search_doctors(
    db: Session,
    params: DoctorSearchParams,
    limit: int = 10,
    offset: int = 0
) -> Tuple[List[Doctor], int]:
    """
    البحث عن الأطباء باستخدام معايير متعددة
    يدعم البحث الجغرافي والتصفية حسب التخصص والتقييم والسعر وغيرها
    """
    query = db.query(Doctor).join(DoctorClinic)
    
    # البحث النصي
    if params.query:
        search_term = f"%{params.query}%"
        query = query.filter(
            or_(
                Doctor.first_name.ilike(search_term),
                Doctor.last_name.ilike(search_term),
                Doctor.bio.ilike(search_term),
                Doctor.specializations.any(search_term)
            )
        )
    
    # التصفية حسب التخصص
    if params.specialization:
        query = query.filter(Doctor.specializations.any(params.specialization))
    
    # التصفية حسب المدينة
    if params.city:
        query = query.filter(DoctorClinic.city == params.city)
    
    # التصفية حسب نوع الاستشارة
    if params.consultation_type:
        query = query.filter(Doctor.consultation_types.any(params.consultation_type))
    
    # التصفية حسب التقييم
    if params.min_rating is not None:
        query = query.filter(Doctor.rating >= params.min_rating)
    
    # التصفية حسب السعر
    if params.max_price is not None:
        query = query.filter(
            or_(
                Doctor.consultation_fees['in_person'].astext.cast(float) <= params.max_price,
                Doctor.consultation_fees['video'].astext.cast(float) <= params.max_price,
                Doctor.consultation_fees['chat'].astext.cast(float) <= params.max_price
            )
        )
    
    # التصفية حسب شركة التأمين
    if params.insurance_provider:
        query = query.filter(Doctor.insurance_providers.any(params.insurance_provider))
    
    # التصفية حسب اللغة
    if params.language:
        query = query.filter(Doctor.languages.any(params.language))
    
    # التصفية حسب الجنس
    if params.gender:
        query = query.filter(Doctor.gender == params.gender)
    
    # البحث الجغرافي
    if params.location:
        # تحويل نصف القطر إلى كيلومترات إذا كان بالميل
        search_radius_km = params.radius_km
        if params.distance_unit == DistanceUnit.MILES:
            search_radius_km = params.radius_km / KM_TO_MILES
        
        # تحويل نقطة البحث إلى جغرافيا
        search_point = func.ST_SetSRID(
            func.ST_MakePoint(params.location.longitude, params.location.latitude),
            4326
        )
        
        # حساب المسافة وتصفية النتائج
        distance = func.ST_Distance(
            cast(DoctorClinic.location, Geography),
            cast(search_point, Geography)
        ) / 1000  # تحويل من متر إلى كيلومتر
        
        query = query.filter(distance <= search_radius_km)
        
        # إضافة المسافة إلى النتائج
        query = query.add_columns(distance.label('distance_km'))
        query = query.order_by(distance)
    
    # حساب إجمالي النتائج
    total = query.count()
    
    # تطبيق الترتيب والتقسيم
    if not params.location:
        query = query.order_by(Doctor.rating.desc())
    query = query.offset(offset).limit(limit)
    
    # تجهيز النتائج
    results = []
    for row in query.all():
        if params.location:
            doctor, distance_km = row
            doctor.distance = format_distance(distance_km, params.distance_unit)
            results.append(doctor)
        else:
            results.append(row)
    
    return results, total

def search_hospitals(
    db: Session,
    params: HospitalSearchParams,
    limit: int = 10,
    offset: int = 0
) -> Tuple[List[Hospital], int]:
    """
    البحث عن المستشفيات باستخدام معايير متعددة
    يدعم البحث الجغرافي والتصفية حسب التخصص والتقييم وغيرها
    """
    query = db.query(Hospital)
    
    # البحث النصي
    if params.query:
        search_term = f"%{params.query}%"
        query = query.filter(
            or_(
                Hospital.name.ilike(search_term),
                Hospital.departments.any(search_term),
                Hospital.specialties.any(search_term)
            )
        )
    
    # التصفية حسب النوع
    if params.type:
        query = query.filter(Hospital.type == params.type)
    
    # التصفية حسب المدينة
    if params.city:
        query = query.filter(Hospital.city == params.city)
    
    # التصفية حسب التخصص
    if params.specialty:
        query = query.filter(Hospital.specialties.any(params.specialty))
    
    # التصفية حسب التقييم
    if params.min_rating is not None:
        query = query.filter(Hospital.rating >= params.min_rating)
    
    # التصفية حسب شركة التأمين
    if params.insurance_provider:
        query = query.filter(Hospital.insurance_providers.any(params.insurance_provider))
    
    # التصفية حسب توفر قسم الطوارئ
    if params.has_emergency:
        query = query.filter(Hospital.emergency_phone.isnot(None))
    
    # البحث الجغرافي
    if params.location and params.radius_km:
        # تحويل نقطة البحث إلى جغرافيا
        search_point = func.ST_SetSRID(
            func.ST_MakePoint(params.location.longitude, params.location.latitude),
            4326
        )
        
        # حساب المسافة وتصفية النتائج
        distance = func.ST_Distance(
            cast(Hospital.location, Geography),
            cast(search_point, Geography)
        )
        
        query = query.filter(distance <= params.radius_km * 1000)  # تحويل إلى أمتار
        query = query.order_by(distance)
    
    # حساب إجمالي النتائج
    total = query.count()
    
    # تطبيق الترتيب والتقسيم
    query = query.order_by(Hospital.rating.desc())
    query = query.offset(offset).limit(limit)
    
    return query.all(), total
