# توثيق API

## نظرة عامة
يوفر API الخاص بنا واجهة RESTful كاملة لجميع وظائف النظام. يستخدم API معيار OpenAPI 3.0 ويدعم المصادقة باستخدام JWT.

## المصادقة

### الحصول على رمز الوصول
```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password"
}
```

استجابة ناجحة:
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer",
    "expires_in": 900
}
```

### تجديد الرمز
```http
POST /api/v1/auth/refresh
Authorization: Bearer {refresh_token}
```

## نقاط النهاية الرئيسية

### المستخدمين

#### تسجيل مستخدم جديد
```http
POST /api/v1/users
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "secure_password",
    "first_name": "John",
    "last_name": "Doe",
    "role": "patient"
}
```

#### تحديث الملف الشخصي
```http
PUT /api/v1/users/me
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890"
}
```

### الأطباء

#### البحث عن الأطباء
```http
GET /api/v1/doctors/search?specialty=cardiology&location=lat,lng&radius=5
Authorization: Bearer {access_token}
```

استجابة:
```json
{
    "doctors": [
        {
            "id": "uuid",
            "name": "Dr. Smith",
            "specialty": "cardiology",
            "rating": 4.5,
            "distance": 2.3,
            "available_slots": [
                "2024-03-20T09:00:00Z",
                "2024-03-20T10:00:00Z"
            ]
        }
    ],
    "total": 10,
    "page": 1
}
```

#### حجز موعد
```http
POST /api/v1/appointments
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "doctor_id": "uuid",
    "datetime": "2024-03-20T09:00:00Z",
    "type": "consultation",
    "symptoms": "Chest pain",
    "notes": "First visit"
}
```

### المدفوعات

#### إنشاء دفعة
```http
POST /api/v1/payments
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "amount": 100.00,
    "currency": "USD",
    "payment_method_id": "pm_card_visa",
    "service_type": "consultation",
    "service_id": "appointment_uuid"
}
```

#### استرداد المبلغ
```http
POST /api/v1/payments/{payment_id}/refund
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "amount": 100.00,
    "reason": "appointment_cancelled"
}
```

### الأدوية

#### البحث عن الأدوية
```http
GET /api/v1/medications/search?query=aspirin&country=US
Authorization: Bearer {access_token}
```

#### إنشاء وصفة طبية
```http
POST /api/v1/prescriptions
Authorization: Bearer {access_token}
Content-Type: application/json

{
    "patient_id": "uuid",
    "medication_id": "uuid",
    "dosage": "100mg",
    "frequency": "twice_daily",
    "duration_days": 30,
    "notes": "Take with food"
}
```

## المخططات (Schemas)

### User
```json
{
    "id": "uuid",
    "email": "string",
    "first_name": "string",
    "last_name": "string",
    "role": "enum(patient, doctor)",
    "is_active": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
}
```

### Doctor
```json
{
    "id": "uuid",
    "user_id": "uuid",
    "specialty": "string",
    "license_number": "string",
    "education": ["string"],
    "experience_years": "integer",
    "rating": "float",
    "consultation_fee": "decimal",
    "available_slots": ["datetime"]
}
```

### Appointment
```json
{
    "id": "uuid",
    "doctor_id": "uuid",
    "patient_id": "uuid",
    "datetime": "datetime",
    "status": "enum(scheduled, completed, cancelled)",
    "type": "enum(consultation, follow_up)",
    "notes": "string",
    "created_at": "datetime"
}
```

## معالجة الأخطاء

### أكواد الحالة
- `200`: نجاح
- `201`: تم الإنشاء
- `400`: طلب غير صالح
- `401`: غير مصرح
- `403`: ممنوع
- `404`: غير موجود
- `422`: خطأ في التحقق
- `429`: تجاوز حد الطلبات
- `500`: خطأ في الخادم

### مثال للخطأ
```json
{
    "error": {
        "code": "VALIDATION_ERROR",
        "message": "Invalid input data",
        "details": {
            "email": ["Invalid email format"]
        }
    }
}
```

## التصفح والترتيب

### معلمات التصفح
- `page`: رقم الصفحة (افتراضي: 1)
- `per_page`: عدد العناصر في الصفحة (افتراضي: 20)
- `sort`: حقل الترتيب
- `order`: اتجاه الترتيب (asc/desc)

مثال:
```http
GET /api/v1/doctors?page=2&per_page=10&sort=rating&order=desc
```

## التحديثات المباشرة
يدعم API تحديثات WebSocket للميزات التالية:
- حالة المواعيد
- الرسائل الفورية
- إشعارات النظام

### الاتصال بـ WebSocket
```javascript
const ws = new WebSocket('wss://api.example.com/ws');
ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    // معالجة التحديث
};
```

## حدود معدل الطلبات
- 100 طلب/دقيقة للمستخدمين العاديين
- 1000 طلب/دقيقة للأطباء
- 10000 طلب/دقيقة للنظام

## الأمان
- جميع الطلبات يجب أن تستخدم HTTPS
- رموز JWT صالحة لمدة 15 دقيقة
- يجب تضمين رمز CSRF في الطلبات غير GET
