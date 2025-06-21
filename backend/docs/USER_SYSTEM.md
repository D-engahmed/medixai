# نظام إدارة المستخدمين

## نظرة عامة
نظام إدارة المستخدمين هو المسؤول عن إدارة حسابات المستخدمين، المصادقة، والتفويض في النظام. يدعم النظام نوعين من المستخدمين: المرضى والأطباء.

## هيكل الملفات
```
app/
├── models/
│   └── user.py           # نموذج بيانات المستخدم
├── schemas/
│   └── user.py          # مخططات التحقق من صحة البيانات
├── api/v1/
│   ├── auth.py          # نقاط نهاية المصادقة
│   └── users.py         # نقاط نهاية إدارة المستخدمين
├── services/
│   ├── auth_service.py  # خدمات المصادقة
│   └── user_service.py  # خدمات إدارة المستخدمين
└── core/
    └── security.py      # وظائف الأمان والتشفير
```

## نموذج البيانات (User Model)
### الحقول الرئيسية
- `id`: UUID (المفتاح الأساسي)
- `email`: البريد الإلكتروني (فريد)
- `password_hash`: كلمة المرور المشفرة
- `role`: نوع المستخدم (PATIENT/DOCTOR)
- `is_active`: حالة الحساب
- `email_verified`: حالة التحقق من البريد
- `two_fa_enabled`: حالة التحقق بخطوتين
- `preferences`: تفضيلات المستخدم (JSON)

### العلاقات
- `patient_profile`: علاقة مع نموذج المريض (1:1)
- `doctor_profile`: علاقة مع نموذج الطبيب (1:1)
- `appointments`: علاقة مع المواعيد (1:n)
- `chat_sessions`: علاقة مع جلسات المحادثة (1:n)

## خدمات المصادقة (Authentication Services)

### المصادقة الأساسية
```python
async def authenticate_user(email: str, password: str) -> User:
    # التحقق من صحة بيانات الاعتماد
    # إنشاء رمز JWT
```

### التحقق بخطوتين (2FA)
```python
async def setup_2fa(user_id: UUID) -> str:
    # إنشاء سر TOTP
    # إنشاء رمز QR
```

### تجديد الرمز (Token Refresh)
```python
async def refresh_token(refresh_token: str) -> Tokens:
    # التحقق من صلاحية رمز التجديد
    # إنشاء رموز جديدة
```

## نقاط النهاية (API Endpoints)

### المصادقة
- `POST /api/v1/auth/login`: تسجيل الدخول
- `POST /api/v1/auth/refresh`: تجديد الرمز
- `POST /api/v1/auth/logout`: تسجيل الخروج
- `POST /api/v1/auth/setup-2fa`: إعداد التحقق بخطوتين
- `POST /api/v1/auth/verify-2fa`: التحقق من رمز 2FA

### إدارة المستخدمين
- `POST /api/v1/users`: إنشاء مستخدم جديد
- `GET /api/v1/users/me`: عرض الملف الشخصي
- `PUT /api/v1/users/me`: تحديث الملف الشخصي
- `PATCH /api/v1/users/me/password`: تغيير كلمة المرور
- `PATCH /api/v1/users/me/preferences`: تحديث التفضيلات

## تدفق البيانات

### تسجيل مستخدم جديد
1. استلام بيانات التسجيل
2. التحقق من صحة البيانات (schema validation)
3. التحقق من عدم وجود البريد الإلكتروني
4. تشفير كلمة المرور
5. إنشاء سجل المستخدم
6. إنشاء الملف الشخصي (مريض/طبيب)
7. إرسال بريد التحقق
8. إرجاع رمز JWT

### تسجيل الدخول
1. استلام بيانات الاعتماد
2. التحقق من وجود المستخدم
3. التحقق من كلمة المرور
4. التحقق من حالة الحساب
5. التحقق من 2FA (إذا كان مفعلاً)
6. إنشاء وإرجاع الرموز

## الأمان

### تشفير كلمة المرور
- استخدام Argon2 لتشفير كلمات المرور
- معاملات التشفير قابلة للتكوين

### رموز JWT
- رمز الوصول: صالح لمدة 15 دقيقة
- رمز التجديد: صالح لمدة 30 يوم
- تشفير RS256 مع مفاتيح RSA

### التحقق بخطوتين
- خوارزمية TOTP
- رموز لمرة واحدة صالحة لمدة 30 ثانية
- دعم تطبيقات Google Authenticator

## التحقق من الصحة
```python
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: UserRole
    
    @validator('password')
    def password_strength(cls, v):
        # التحقق من قوة كلمة المرور
```

## الاختبارات
```python
async def test_user_registration():
    # اختبار تسجيل مستخدم جديد
    
async def test_user_login():
    # اختبار تسجيل الدخول
    
async def test_password_reset():
    # اختبار إعادة تعيين كلمة المرور
``` 