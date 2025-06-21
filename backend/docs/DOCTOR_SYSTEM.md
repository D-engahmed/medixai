# نظام إدارة الأطباء

## نظرة عامة
نظام إدارة الأطباء يتحكم في كل ما يتعلق بالأطباء في المنصة، بما في ذلك الملفات الشخصية، الجداول، التخصصات، والتقييمات.

## هيكل الملفات
```
app/
├── models/
│   └── doctor.py           # نموذج بيانات الطبيب
├── schemas/
│   └── doctor.py          # مخططات التحقق من صحة البيانات
├── api/v1/
│   └── doctors.py         # نقاط نهاية API الخاصة بالأطباء
├── services/
│   ├── doctor_service.py  # خدمات إدارة الأطباء
│   └── geo_service.py     # خدمات البحث الجغرافي
└── utils/
    └── validators.py      # التحقق من صحة البيانات المتخصصة
```

## نموذج البيانات (Doctor Model)

### الحقول الرئيسية
```python
class Doctor(Base):
    id: UUID
    user_id: UUID          # العلاقة مع نموذج المستخدم
    license_number: str    # رقم الترخيص الطبي
    specialization: str    # التخصص
    years_experience: int  # سنوات الخبرة
    education: JSON        # المؤهلات التعليمية
    certifications: JSON   # الشهادات المهنية
    working_hours: JSON    # ساعات العمل
    consultation_fee: Decimal # رسوم الاستشارة
    location: Point        # الموقع الجغرافي
    rating: Decimal       # متوسط التقييم
    total_reviews: int    # عدد التقييمات
```

### العلاقات
- `user`: علاقة مع نموذج المستخدم (1:1)
- `appointments`: علاقة مع المواعيد (1:n)
- `specialties`: علاقة مع التخصصات (n:n)
- `hospitals`: علاقة مع المستشفيات (n:n)
- `reviews`: علاقة مع التقييمات (1:n)

## الخدمات (Services)

### خدمة إدارة الأطباء
```python
class DoctorService:
    async def create_doctor(data: DoctorCreate) -> Doctor:
        # إنشاء ملف طبيب جديد
        
    async def update_doctor(id: UUID, data: DoctorUpdate) -> Doctor:
        # تحديث بيانات الطبيب
        
    async def get_doctor_availability(id: UUID, date: date) -> List[TimeSlot]:
        # الحصول على المواعيد المتاحة
        
    async def update_working_hours(id: UUID, hours: WorkingHours) -> Doctor:
        # تحديث ساعات العمل
```

### خدمة البحث الجغرافي
```python
class GeoService:
    async def find_nearby_doctors(
        lat: float,
        lng: float,
        radius: int,
        specialty: Optional[str] = None
    ) -> List[Doctor]:
        # البحث عن الأطباء القريبين
```

## نقاط النهاية (API Endpoints)

### إدارة الملف الشخصي
- `POST /api/v1/doctors`: إنشاء ملف طبيب
- `GET /api/v1/doctors/{id}`: عرض ملف طبيب
- `PUT /api/v1/doctors/{id}`: تحديث ملف طبيب
- `DELETE /api/v1/doctors/{id}`: حذف ملف طبيب

### جدول المواعيد
- `GET /api/v1/doctors/{id}/availability`: عرض المواعيد المتاحة
- `PUT /api/v1/doctors/{id}/working-hours`: تحديث ساعات العمل
- `GET /api/v1/doctors/{id}/appointments`: عرض المواعيد المحجوزة

### البحث والتصفية
- `GET /api/v1/doctors/search`: البحث عن الأطباء
- `GET /api/v1/doctors/nearby`: البحث عن الأطباء القريبين
- `GET /api/v1/doctors/specialties`: عرض التخصصات المتاحة

### التقييمات والمراجعات
- `GET /api/v1/doctors/{id}/reviews`: عرض التقييمات
- `POST /api/v1/doctors/{id}/reviews`: إضافة تقييم جديد

## تدفق البيانات

### تسجيل طبيب جديد
1. التحقق من بيانات التسجيل
2. التحقق من رقم الترخيص
3. إنشاء حساب مستخدم
4. إنشاء ملف طبيب
5. ربط التخصصات والمستشفيات
6. تفعيل الحساب بعد التحقق

### البحث عن الأطباء
1. استلام معايير البحث
2. تطبيق الفلترة الجغرافية
3. تطبيق فلترة التخصص
4. ترتيب النتائج حسب المسافة/التقييم
5. إرجاع النتائج مع التفاصيل

### حجز موعد
1. التحقق من توفر الموعد
2. حجز الفترة الزمنية
3. إنشاء سجل الموعد
4. إرسال التأكيدات
5. تحديث جدول الطبيب

## لوحة التحكم

### المؤشرات الرئيسية
- عدد المواعيد اليومية
- متوسط مدة الاستشارة
- معدل الإلغاء
- الدخل الشهري
- تقييمات المرضى

### التقارير
- تقرير المواعيد
- تقرير الدخل
- تحليل التقييمات
- إحصائيات المرضى

## الأمان والتحقق

### التحقق من الترخيص
```python
async def verify_license(license_number: str, country: str) -> bool:
    # التحقق من صحة رقم الترخيص مع الهيئات الرسمية
```

### التحقق من المؤهلات
```python
async def verify_credentials(credentials: List[Credential]) -> bool:
    # التحقق من صحة المؤهلات والشهادات
```

## الاختبارات
```python
class TestDoctorSystem:
    async def test_doctor_registration(self):
        # اختبار تسجيل طبيب جديد
        
    async def test_availability_management(self):
        # اختبار إدارة المواعيد المتاحة
        
    async def test_geo_search(self):
        # اختبار البحث الجغرافي
``` 