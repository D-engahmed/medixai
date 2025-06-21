"""
User Service Module
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
import pyotp
import qrcode
import io
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.models.user import User, Patient, Doctor, UserSession, UserRole
from app.schemas.user import UserCreate, UserUpdate, PatientCreate, DoctorCreate
from app.core.security import create_jwt_token, verify_password, get_password_hash
from app.core.config import settings
from app.utils.logger import logger

class UserService:
    def __init__(self, db: Session):
        self.db = db
        self.ph = PasswordHasher()
    
    def create_user(self, user_data: UserCreate) -> User:
        """إنشاء مستخدم جديد"""
        # التحقق من وجود البريد الإلكتروني
        if self.get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="البريد الإلكتروني مستخدم بالفعل"
            )
        
        # إنشاء مستخدم جديد
        db_user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role
        )
        
        try:
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            # إرسال بريد التحقق
            self._send_verification_email(db_user)
            
            return db_user
        except Exception as e:
            self.db.rollback()
            logger.error(f"خطأ في إنشاء المستخدم: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="حدث خطأ أثناء إنشاء المستخدم"
            )
    
    def create_patient(self, patient_data: PatientCreate) -> Patient:
        """إنشاء مريض جديد"""
        # إنشاء المستخدم أولاً
        user = self.create_user(patient_data.user)
        
        # إنشاء المريض
        db_patient = Patient(
            user_id=user.id,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            phone=patient_data.phone,
            address=patient_data.address,
            medical_history=patient_data.medical_history,
            allergies=patient_data.allergies,
            current_medications=patient_data.current_medications,
            emergency_contact=patient_data.emergency_contact,
            insurance_provider=patient_data.insurance_provider,
            insurance_policy_number=patient_data.insurance_policy_number,
            preferred_language=patient_data.preferred_language,
            notification_preferences=patient_data.notification_preferences
        )
        
        try:
            self.db.add(db_patient)
            self.db.commit()
            self.db.refresh(db_patient)
            return db_patient
        except Exception as e:
            self.db.rollback()
            # حذف المستخدم في حالة فشل إنشاء المريض
            self.db.delete(user)
            self.db.commit()
            logger.error(f"خطأ في إنشاء المريض: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="حدث خطأ أثناء إنشاء المريض"
            )
    
    def create_doctor(self, doctor_data: DoctorCreate) -> Doctor:
        """إنشاء طبيب جديد"""
        # إنشاء المستخدم أولاً
        user = self.create_user(doctor_data.user)
        
        # إنشاء الطبيب
        db_doctor = Doctor(
            user_id=user.id,
            license_number=doctor_data.license_number,
            specialization=doctor_data.specialization,
            years_experience=doctor_data.years_experience,
            consultation_fee=doctor_data.consultation_fee,
            phone=doctor_data.phone,
            address=doctor_data.address,
            bio=doctor_data.bio,
            qualifications=doctor_data.qualifications,
            languages_spoken=doctor_data.languages_spoken,
            availability_hours=doctor_data.availability_hours,
            timezone=doctor_data.timezone
        )
        
        try:
            self.db.add(db_doctor)
            self.db.commit()
            self.db.refresh(db_doctor)
            return db_doctor
        except Exception as e:
            self.db.rollback()
            # حذف المستخدم في حالة فشل إنشاء الطبيب
            self.db.delete(user)
            self.db.commit()
            logger.error(f"خطأ في إنشاء الطبيب: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="حدث خطأ أثناء إنشاء الطبيب"
            )
    
    def authenticate_user(self, email: str, password: str) -> Tuple[User, str, str]:
        """مصادقة المستخدم وإنشاء توكن"""
        user = self.get_user_by_email(email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="الحساب غير نشط"
            )
        
        try:
            if not verify_password(password, user.password_hash):
                self._handle_failed_login(user)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
                )
        except VerifyMismatchError:
            self._handle_failed_login(user)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="البريد الإلكتروني أو كلمة المرور غير صحيحة"
            )
        
        # إعادة تعيين محاولات تسجيل الدخول الفاشلة
        if user.failed_login_attempts > 0:
            user.failed_login_attempts = 0
            user.account_locked_until = None
            self.db.commit()
        
        # تحديث آخر تسجيل دخول
        user.last_login = datetime.utcnow()
        self.db.commit()
        
        # إنشاء توكن
        access_token = create_jwt_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        refresh_token = create_jwt_token(
            data={"sub": str(user.id), "role": user.role.value},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        # حفظ الجلسة
        self._create_session(user, access_token, refresh_token)
        
        return user, access_token, refresh_token
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """الحصول على المستخدم بواسطة المعرف"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """الحصول على المستخدم بواسطة البريد الإلكتروني"""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user_id: UUID, user_data: UserUpdate) -> User:
        """تحديث بيانات المستخدم"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المستخدم غير موجود"
            )
        
        # تحديث البيانات
        for field, value in user_data.dict(exclude_unset=True).items():
            setattr(user, field, value)
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"خطأ في تحديث المستخدم: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="حدث خطأ أثناء تحديث المستخدم"
            )
    
    def delete_user(self, user_id: UUID) -> bool:
        """حذف المستخدم"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المستخدم غير موجود"
            )
        
        try:
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"خطأ في حذف المستخدم: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="حدث خطأ أثناء حذف المستخدم"
            )
    
    def setup_2fa(self, user_id: UUID) -> Dict[str, Any]:
        """إعداد المصادقة الثنائية"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="المستخدم غير موجود"
            )
        
        # إنشاء سر TOTP
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        
        # إنشاء رابط URI
        provisioning_uri = totp.provisioning_uri(
            name=user.email,
            issuer_name=settings.APP_NAME
        )
        
        # إنشاء QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        img_buffer = io.BytesIO()
        img.save(img_buffer, format="PNG")
        qr_code = img_buffer.getvalue()
        
        # حفظ السر في قاعدة البيانات
        user.two_fa_secret = secret
        self.db.commit()
        
        return {
            "secret": secret,
            "qr_code": qr_code,
            "provisioning_uri": provisioning_uri
        }
    
    def verify_2fa(self, user_id: UUID, code: str) -> bool:
        """التحقق من رمز المصادقة الثنائية"""
        user = self.get_user_by_id(user_id)
        if not user or not user.two_fa_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="المصادقة الثنائية غير مفعلة"
            )
        
        totp = pyotp.TOTP(user.two_fa_secret)
        if not totp.verify(code):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="رمز غير صحيح"
            )
        
        # تفعيل المصادقة الثنائية
        user.two_fa_enabled = True
        self.db.commit()
        
        return True
    
    def _handle_failed_login(self, user: User) -> None:
        """معالجة محاولة تسجيل الدخول الفاشلة"""
        user.failed_login_attempts += 1
        
        # قفل الحساب بعد 5 محاولات فاشلة
        if user.failed_login_attempts >= 5:
            user.account_locked_until = datetime.utcnow() + timedelta(minutes=30)
        
        self.db.commit()
    
    def _create_session(self, user: User, access_token: str, refresh_token: str) -> UserSession:
        """إنشاء جلسة مستخدم جديدة"""
        session = UserSession(
            user_id=user.id,
            session_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        self.db.add(session)
        self.db.commit()
        return session
    
    def _send_verification_email(self, user: User) -> None:
        """إرسال بريد التحقق"""
        # TODO: تنفيذ إرسال البريد الإلكتروني
        pass
