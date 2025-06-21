# نظام إدارة الأدوية

## نظرة عامة
نظام إدارة الأدوية مسؤول عن إدارة قاعدة بيانات الأدوية، الوصفات الطبية، والتحقق من التفاعلات الدوائية.

## هيكل الملفات
```
app/
├── models/
│   ├── medication.py        # نموذج بيانات الدواء
│   └── prescription.py      # نموذج الوصفة الطبية
├── schemas/
│   ├── medication.py        # مخططات التحقق
│   └── prescription.py      # مخططات الوصفات
├── api/v1/
│   └── medications.py       # نقاط نهاية API
├── services/
│   ├── medication_service.py # خدمات الأدوية
│   └── interaction_service.py # خدمة التفاعلات
└── utils/
    └── drug_validator.py    # التحقق من صحة الأدوية
```

## نماذج البيانات

### نموذج الدواء (Medication)
```python
class Medication(Base):
    id: UUID
    name: str
    generic_name: str
    manufacturer: str
    description: Text
    dosage_forms: List[str]
    strength: str
    therapeutic_class: str
    controlled_substance: bool
    prescription_required: bool
    side_effects: List[str]
    contraindications: List[str]
    interactions: List[str]
    storage_conditions: str
    price: Decimal
    stock_level: int
    country_availability: List[str]
    created_at: datetime
    updated_at: datetime
```

### نموذج الوصفة الطبية (Prescription)
```python
class Prescription(Base):
    id: UUID
    patient_id: UUID
    doctor_id: UUID
    medication_id: UUID
    dosage: str
    frequency: str
    duration_days: int
    quantity: int
    refills: int
    instructions: Text
    status: PrescriptionStatus
    issued_at: datetime
    valid_until: datetime
    filled_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
```

## الخدمات

### خدمة الأدوية
```python
class MedicationService:
    async def search_medications(
        query: str,
        country: str,
        require_prescription: bool = None
    ) -> List[Medication]:
        # البحث عن الأدوية
        
    async def check_availability(
        medication_id: UUID,
        quantity: int
    ) -> bool:
        # التحقق من التوفر
        
    async def update_stock(
        medication_id: UUID,
        quantity: int,
        operation: StockOperation
    ) -> Medication:
        # تحديث المخزون
```

### خدمة التفاعلات الدوائية
```python
class InteractionService:
    async def check_interactions(
        medications: List[UUID]
    ) -> List[DrugInteraction]:
        # التحقق من التفاعلات
        
    async def validate_prescription(
        prescription: Prescription,
        patient_history: PatientHistory
    ) -> ValidationResult:
        # التحقق من صحة الوصفة
```

## نقاط النهاية API

### إدارة الأدوية
```python
@router.get("/medications/search")
async def search_medications(
    query: str,
    country: str,
    prescription: bool = None
) -> List[MedicationResponse]:
    # البحث عن الأدوية

@router.get("/medications/{id}")
async def get_medication(
    id: UUID
) -> MedicationResponse:
    # عرض تفاصيل الدواء
```

### إدارة الوصفات
```python
@router.post("/prescriptions")
async def create_prescription(
    data: PrescriptionCreate
) -> PrescriptionResponse:
    # إنشاء وصفة جديدة

@router.get("/prescriptions/{id}")
async def get_prescription(
    id: UUID
) -> PrescriptionResponse:
    # عرض تفاصيل الوصفة
```

## تدفق البيانات

### إنشاء وصفة طبية
1. التحقق من صلاحية الطبيب
2. التحقق من توفر الدواء
3. فحص التفاعلات الدوائية
4. إنشاء الوصفة
5. تحديث المخزون
6. إرسال الإشعارات

### صرف وصفة طبية
1. التحقق من صلاحية الوصفة
2. التحقق من المخزون
3. تحديث حالة الوصفة
4. تحديث المخزون
5. إنشاء فاتورة
6. إرسال التعليمات

## التحقق من الصحة

### التحقق من الوصفة
```python
class PrescriptionValidator:
    def validate_dosage(
        medication: Medication,
        dosage: str,
        patient_weight: float
    ) -> bool:
        # التحقق من صحة الجرعة
        
    def validate_frequency(
        medication: Medication,
        frequency: str
    ) -> bool:
        # التحقق من صحة التكرار
```

### التحقق من التفاعلات
```python
class InteractionValidator:
    def check_drug_interactions(
        medications: List[Medication]
    ) -> List[Interaction]:
        # فحص التفاعلات بين الأدوية
        
    def check_allergies(
        medication: Medication,
        patient_allergies: List[str]
    ) -> List[str]:
        # فحص الحساسية
```

## المراقبة والتقارير

### مراقبة المخزون
```python
async def monitor_stock_levels():
    # مراقبة مستويات المخزون
    # إرسال تنبيهات عند انخفاض المخزون
```

### تقارير الأدوية
```python
async def generate_medication_report(
    start_date: date,
    end_date: date
) -> MedicationReport:
    # إنشاء تقرير استخدام الأدوية
```

## الأمان والامتثال

### التحقق من الصلاحيات
```python
def verify_prescription_authority(
    doctor: Doctor,
    medication: Medication
) -> bool:
    # التحقق من صلاحية الطبيب لوصف الدواء
```

### تتبع المواد المراقبة
```python
async def track_controlled_substance(
    prescription: Prescription
) -> None:
    # تتبع وتسجيل صرف المواد المراقبة
```

## الاختبارات
```python
class TestMedicationSystem:
    async def test_medication_search(self):
        # اختبار البحث عن الأدوية
        
    async def test_prescription_creation(self):
        # اختبار إنشاء الوصفات
        
    async def test_interaction_check(self):
        # اختبار فحص التفاعلات
```

## التكامل مع الأنظمة الأخرى

### نظام المدفوعات
```python
async def process_medication_payment(
    prescription: Prescription
) -> Payment:
    # معالجة دفع الأدوية
```

### نظام الإشعارات
```python
async def send_prescription_notifications(
    prescription: Prescription
) -> None:
    # إرسال إشعارات الوصفة
``` 