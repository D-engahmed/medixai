# نظام إدارة المستخدمين

## نظرة عامة
نظام إدارة المستخدمين هو العمود الفقري للمنصة الطبية، حيث يدير حسابات المستخدمين، المصادقة، والتفويض. يدعم النظام نوعين رئيسيين من المستخدمين: المرضى والأطباء.

## هيكل النظام

### المكونات الرئيسية
```
app/
├── models/
│   ├── user.py              # نموذج المستخدم الأساسي
│   ├── patient.py           # نموذج المريض
│   └── doctor.py            # نموذج الطبيب
├── schemas/
│   ├── user.py             # مخططات المستخدم
│   └── auth.py             # مخططات المصادقة
├── api/v1/
│   ├── auth.py             # نقاط نهاية المصادقة
│   └── users.py            # نقاط نهاية المستخدمين
└── services/
    ├── auth_service.py     # خدمات المصادقة
    └── user_service.py     # خدمات المستخدمين
```

## نماذج البيانات

### نموذج المستخدم الأساسي
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True)
    password_hash = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    two_fa_enabled = Column(Boolean, default=False)
    two_fa_secret = Column(String, nullable=True)
    preferences = Column(JSONB, default={})
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

### نموذج المريض
```python
class Patient(Base):
    __tablename__ = "patients"
    
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id"))
    date_of_birth = Column(Date)
    gender = Column(Enum(Gender))
    blood_type = Column(String)
    allergies = Column(ARRAY(String))
    medical_conditions = Column(ARRAY(String))
    emergency_contact = Column(JSONB)
    insurance_info = Column(JSONB)
    address = Column(JSONB)
    
    # العلاقات
    user = relationship("User", back_populates="patient_profile")
    appointments = relationship("Appointment", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")
```

## خدمات النظام

### خدمة المصادقة
```python
class AuthService:
    async def authenticate_user(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str]:
        """المصادقة على المستخدم وإنشاء رمز JWT"""
        
    async def create_refresh_token(
        self,
        user_id: UUID
    ) -> str:
        """إنشاء رمز تجديد"""
        
    async def verify_2fa(
        self,
        user: User,
        code: str
    ) -> bool:
        """التحقق من رمز 2FA"""
```

### خدمة المستخدمين
```python
class UserService:
    async def create_user(
        self,
        data: UserCreate
    ) -> User:
        """إنشاء مستخدم جديد"""
        
    async def update_user(
        self,
        user_id: UUID,
        data: UserUpdate
    ) -> User:
        """تحديث بيانات المستخدم"""
        
    async def update_preferences(
        self,
        user_id: UUID,
        preferences: Dict
    ) -> User:
        """تحديث تفضيلات المستخدم"""
```

## تدفقات العمل الرئيسية

### تسجيل مستخدم جديد
1. التحقق من صحة البيانات
2. التحقق من عدم وجود البريد الإلكتروني
3. تشفير كلمة المرور
4. إنشاء سجل المستخدم
5. إنشاء الملف الشخصي (مريض/طبيب)
6. إرسال بريد التحقق
7. إرجاع بيانات المستخدم

### تسجيل الدخول
1. التحقق من بيانات الاعتماد
2. فحص حالة الحساب
3. التحقق من 2FA (إذا كان مفعلاً)
4. إنشاء رموز JWT
5. تحديث آخر تسجيل دخول
6. تسجيل محاولة الدخول

### تحديث الملف الشخصي
1. التحقق من الصلاحيات
2. التحقق من صحة البيانات
3. تحديث البيانات
4. تحديث الفهرس
5. إرسال إشعار التحديث

## إدارة الجلسات

### تخزين الجلسات في Redis
```python
class SessionManager:
    async def create_session(
        self,
        user_id: UUID,
        device_info: Dict
    ) -> str:
        """إنشاء جلسة جديدة"""
        
    async def validate_session(
        self,
        session_id: str
    ) -> bool:
        """التحقق من صلاحية الجلسة"""
```

### إدارة الرموز
```python
class TokenManager:
    def create_access_token(
        self,
        user_id: UUID
    ) -> str:
        """إنشاء رمز وصول"""
        
    def create_refresh_token(
        self,
        user_id: UUID
    ) -> str:
        """إنشاء رمز تجديد"""
```

## الأمان والتحقق

### تشفير كلمة المرور
```python
class PasswordManager:
    def hash_password(
        self,
        password: str
    ) -> str:
        """تشفير كلمة المرور باستخدام Argon2"""
        
    def verify_password(
        self,
        plain_password: str,
        hashed_password: str
    ) -> bool:
        """التحقق من كلمة المرور"""
```

### التحقق بخطوتين
```python
class TwoFactorAuth:
    def generate_secret(self) -> str:
        """إنشاء سر TOTP"""
        
    def verify_code(
        self,
        secret: str,
        code: str
    ) -> bool:
        """التحقق من رمز TOTP"""
```

## التحقق من الصحة

### مخططات المستخدم
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: UserRole
    
    @validator('password')
    def password_strength(cls, v):
        """التحقق من قوة كلمة المرور"""
```

### مخططات المريض
```python
class PatientCreate(BaseModel):
    date_of_birth: date
    gender: Gender
    blood_type: Optional[str]
    allergies: List[str]
    medical_conditions: List[str]
    emergency_contact: EmergencyContact
```

## المراقبة والتدقيق

### سجلات التدقيق
```python
class UserAuditLog:
    user_id: UUID
    action: str
    details: Dict
    ip_address: str
    user_agent: str
    timestamp: datetime
```

### مراقبة النشاط
```python
async def monitor_user_activity():
    """مراقبة نشاط المستخدمين وتحديد الأنماط المشبوهة"""
```

## التكامل مع الأنظمة الأخرى

### نظام الإشعارات
```python
async def send_user_notification(
    user_id: UUID,
    notification_type: str,
    data: Dict
):
    """إرسال إشعار للمستخدم"""
```

### نظام التقارير
```python
async def generate_user_report(
    user_id: UUID,
    report_type: str
) -> Report:
    """إنشاء تقرير عن نشاط المستخدم"""
```

## الاختبارات

### اختبارات الوحدة
```python
class TestUserAuthentication:
    async def test_user_registration(self):
        """اختبار تسجيل مستخدم جديد"""
        
    async def test_user_login(self):
        """اختبار تسجيل الدخول"""
```

### اختبارات التكامل
```python
class TestUserSystem:
    async def test_complete_user_flow(self):
        """اختبار تدفق المستخدم الكامل"""
``` 